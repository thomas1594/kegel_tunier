"""
Helper functions for the bowling tournament app
"""

import io
import os
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

# Database configuration
DB_DIR = os.getenv("DB_DIR", "data")
DB_PATH = os.path.join(DB_DIR, "kegelturnier.db")

# Ensure data directory exists
os.makedirs(DB_DIR, exist_ok=True)

VOLLE_COLS = [f"V{i}" for i in range(1, 11)]
ABR_COLS = [f"A{i}" for i in range(1, 11)]
SCORE_COLS = VOLLE_COLS + ABR_COLS
INTERNAL_COLS = ["_id", "PlayerID"]


# ---------------------------------------------------------------------------
# In-memory data
# ---------------------------------------------------------------------------
def init_players():
    """Initialize player data with 10 throws per category."""
    if "players" not in st.session_state:
        data = []
        for team_id in range(1, 11):
            for player_id in range(1, 6):
                player_data = {
                    "_id": None,
                    "Team": f"Team {team_id}",
                    "Spieler": f"Spieler {player_id}",
                    "Geschlecht": "m",
                }
                for i in range(1, 11):
                    player_data[f"V{i}"] = 0
                for i in range(1, 11):
                    player_data[f"A{i}"] = 0
                data.append(player_data)
        st.session_state.players = pd.DataFrame(data)


def empty_ko_df():
    """Return an empty KO data frame with the expected columns."""
    return pd.DataFrame(
        columns=["_id", "Runde", "Team", "Spieler", "PlayerID"] + SCORE_COLS
    )


def calculate_totals(df):
    """Calculate total values for a DataFrame (in place, like before)."""
    df["Volle"] = df[VOLLE_COLS].sum(axis=1)
    df["Abräumen"] = df[ABR_COLS].sum(axis=1)
    df["Gesamt"] = df["Volle"] + df["Abräumen"]
    return df


# Ordering for ties: total, then spare pins, then full pins, then name.
TEAM_SORT_COLUMNS = ["Gesamt", "Abräumen", "Volle", "Team"]
TEAM_SORT_ASCENDING = [False, False, False, True]
PLAYER_SORT_COLUMNS = ["Gesamt", "Abräumen", "Volle", "Spieler", "Team"]
PLAYER_SORT_ASCENDING = [False, False, False, True, True]


def get_team_scores(df):
    """Calculate team rankings with a deterministic tie-break."""
    if df.empty:
        return pd.DataFrame(columns=["Rang", "Team", "Volle", "Abräumen", "Gesamt"])

    team_scores = df.groupby("Team").agg(
        {"Volle": "sum", "Abräumen": "sum", "Gesamt": "sum"}
    ).reset_index()
    team_scores = team_scores.sort_values(
        TEAM_SORT_COLUMNS, ascending=TEAM_SORT_ASCENDING
    ).reset_index(drop=True)
    team_scores.insert(0, "Rang", range(1, len(team_scores) + 1))
    return team_scores


def get_player_ranking(df, limit=None):
    """Return the player ranking with a deterministic tie-break."""
    if df.empty:
        return pd.DataFrame(
            columns=["Spieler", "Team", "Geschlecht", "Volle", "Abräumen", "Gesamt"]
        )

    ranked = df.sort_values(
        PLAYER_SORT_COLUMNS, ascending=PLAYER_SORT_ASCENDING
    ).reset_index(drop=True)
    columns = ["Spieler", "Team", "Geschlecht", "Volle", "Abräumen", "Gesamt"]
    ranked = ranked[columns]
    if limit is not None:
        ranked = ranked.head(limit).reset_index(drop=True)
    ranked.index = ranked.index + 1
    ranked.index.name = "Rang"
    return ranked


def sorted_teams(players_df):
    """Return team names in their natural (numeric) display order."""

    def key(name):
        suffix = str(name).split()[-1]
        return int(suffix) if suffix.isdigit() else 10**9

    return sorted(dict.fromkeys(players_df["Team"]), key=key)


def next_team_name(existing_names):
    """Return the next free 'Team N' name."""
    used = set(existing_names)
    number = 1
    while f"Team {number}" in used:
        number += 1
    return f"Team {number}"


def resize_teams(players_df, new_count, players_per_team=5):
    """Return a copy of the player data frame with ``new_count`` teams.

    Teams are kept/removed by their data-frame order, so renamed teams are not
    lost when the team count is reduced.
    """
    teams = list(dict.fromkeys(players_df["Team"]))
    if new_count < len(teams):
        keep = set(teams[:new_count])
        return players_df[players_df["Team"].isin(keep)].reset_index(drop=True)

    result = players_df.copy()
    existing = set(result["Team"])
    for _ in range(new_count - len(teams)):
        team_name = next_team_name(existing)
        existing.add(team_name)
        for player_id in range(1, players_per_team + 1):
            row = {
                "_id": None,
                "Team": team_name,
                "Spieler": f"Spieler {player_id}",
                "Geschlecht": "m",
            }
            for column in SCORE_COLS:
                row[column] = 0
            result = pd.concat([result, pd.DataFrame([row])], ignore_index=True)
    return result.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Excel export
# ---------------------------------------------------------------------------
def _public_columns(df):
    return [c for c in df.columns if c not in INTERNAL_COLS and not c.startswith("_")]


def _team_scores_for_export(df):
    clean = df[_public_columns(df)].copy()
    clean = calculate_totals(clean)
    return get_team_scores(clean)


def build_workbook(players_df):
    """Build the Excel workbook and return it as bytes."""
    export_df = players_df[_public_columns(players_df)].copy()
    export_df = calculate_totals(export_df)
    export_df = export_df.rename(
        columns={"Volle": "Volle_Summe", "Abräumen": "Abräumen_Summe"}
    )

    team_scores = _team_scores_for_export(players_df)
    player_ranking = get_player_ranking(
        calculate_totals(players_df[_public_columns(players_df)].copy())
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="Alle Würfe", index=False)
        team_scores.to_excel(writer, sheet_name="Team-Ranking", index=False)
        player_ranking.to_excel(writer, sheet_name="Spieler-Ranking", index=True)
    return buffer.getvalue()


def save_to_excel():
    """Save all data to an Excel file inside the data directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kegelturnier_{timestamp}.xlsx"
    path = os.path.join(DB_DIR, filename)
    with open(path, "wb") as handle:
        handle.write(build_workbook(st.session_state.players))
    return path


def create_excel_download():
    """Create Excel file for download."""
    return build_workbook(st.session_state.players)


# ---------------------------------------------------------------------------
# Edit callbacks
# ---------------------------------------------------------------------------
def update_player_name(idx, team):
    """Callback function for automatically saving player name."""
    key = f"player_name_{team}_{idx}"
    if key not in st.session_state or "players" not in st.session_state:
        return  # Skip if session was reset
    st.session_state.players.at[idx, "Spieler"] = st.session_state[key]
    st.session_state.last_edited_team = team


def update_geschlecht(idx, team):
    """Callback function for automatically saving gender."""
    key = f"geschlecht_edit_{team}_{idx}"
    if key not in st.session_state or "players" not in st.session_state:
        return  # Skip if session was reset
    st.session_state.players.at[idx, "Geschlecht"] = st.session_state[key]
    st.session_state.last_edited_team = team


# ---------------------------------------------------------------------------
# KO (semifinal / final) helpers
# ---------------------------------------------------------------------------
def team_player_entries(players_df, team_name):
    """Return ``(name, player_id)`` tuples for a team in display order."""
    team = players_df[players_df["Team"] == team_name]
    return [
        (row["Spieler"], None if pd.isna(row["_id"]) else int(row["_id"]))
        for _, row in team.iterrows()
    ]


def sync_ko_round(ko_df, runde, assignments):
    """Make the KO rows of ``runde`` match ``assignments``.

    ``assignments`` maps a slot key (e.g. ``HF_Team_1``) to a list of
    ``(player_name, player_id)`` tuples. Scores are preserved when the same
    player id stays in the same slot, and reset when the player changes. This
    keeps renamed players intact while reacting correctly to a changed top 4.
    """
    if ko_df is None or ko_df.empty:
        ko_df = empty_ko_df()
    else:
        ko_df = ko_df.copy()

    for column in ["_id", "PlayerID"] + SCORE_COLS:
        if column not in ko_df.columns:
            ko_df[column] = None

    others = ko_df[ko_df["Runde"] != runde]
    existing = ko_df[ko_df["Runde"] == runde]

    rows = []
    for team_key, players in assignments.items():
        slot_existing = existing[existing["Team"] == team_key]
        by_player_id = {}
        for _, row in slot_existing.iterrows():
            player_id = row.get("PlayerID")
            if pd.notna(player_id):
                by_player_id[int(player_id)] = row

        for player_name, player_id in players:
            new_row = {
                "_id": None,
                "Runde": runde,
                "Team": team_key,
                "Spieler": player_name,
                "PlayerID": player_id,
            }
            for column in SCORE_COLS:
                new_row[column] = 0

            if player_id is not None and int(player_id) in by_player_id:
                previous = by_player_id[int(player_id)]
                if pd.notna(previous.get("_id")):
                    new_row["_id"] = int(previous["_id"])
                for column in SCORE_COLS:
                    new_row[column] = int(previous[column])

            rows.append(new_row)

    new_rows_df = pd.DataFrame(rows)
    if new_rows_df.empty:
        new_rows_df = empty_ko_df()
    return pd.concat([others, new_rows_df], ignore_index=True)


def ko_player_mask(ko_df, runde, team_key, player_id, player_name):
    """Build a mask for a player in a KO slot (id first, name as fallback)."""
    base = (ko_df["Runde"] == runde) & (ko_df["Team"] == team_key)
    if player_id is not None and not pd.isna(player_id):
        mask = base & (ko_df["PlayerID"] == player_id)
        if mask.any():
            return mask
    return base & (ko_df["Spieler"] == player_name)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def init_database():
    """Initialize SQLite database and create/migrate tables if needed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            spieler TEXT NOT NULL,
            geschlecht TEXT DEFAULT 'm',
            v1 INTEGER DEFAULT 0, v2 INTEGER DEFAULT 0, v3 INTEGER DEFAULT 0,
            v4 INTEGER DEFAULT 0, v5 INTEGER DEFAULT 0, v6 INTEGER DEFAULT 0,
            v7 INTEGER DEFAULT 0, v8 INTEGER DEFAULT 0, v9 INTEGER DEFAULT 0,
            v10 INTEGER DEFAULT 0,
            a1 INTEGER DEFAULT 0, a2 INTEGER DEFAULT 0, a3 INTEGER DEFAULT 0,
            a4 INTEGER DEFAULT 0, a5 INTEGER DEFAULT 0, a6 INTEGER DEFAULT 0,
            a7 INTEGER DEFAULT 0, a8 INTEGER DEFAULT 0, a9 INTEGER DEFAULT 0,
            a10 INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ko_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            runde TEXT NOT NULL,
            team TEXT NOT NULL,
            spieler TEXT NOT NULL,
            player_id INTEGER,
            v1 INTEGER DEFAULT 0, v2 INTEGER DEFAULT 0, v3 INTEGER DEFAULT 0,
            v4 INTEGER DEFAULT 0, v5 INTEGER DEFAULT 0, v6 INTEGER DEFAULT 0,
            v7 INTEGER DEFAULT 0, v8 INTEGER DEFAULT 0, v9 INTEGER DEFAULT 0,
            v10 INTEGER DEFAULT 0,
            a1 INTEGER DEFAULT 0, a2 INTEGER DEFAULT 0, a3 INTEGER DEFAULT 0,
            a4 INTEGER DEFAULT 0, a5 INTEGER DEFAULT 0, a6 INTEGER DEFAULT 0,
            a7 INTEGER DEFAULT 0, a8 INTEGER DEFAULT 0, a9 INTEGER DEFAULT 0,
            a10 INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived BOOLEAN DEFAULT 0
        )
        """
    )

    # Migration: add player_id to databases created by older versions.
    cursor.execute("PRAGMA table_info(ko_data)")
    ko_columns = {row[1] for row in cursor.fetchall()}
    if "player_id" not in ko_columns:
        cursor.execute("ALTER TABLE ko_data ADD COLUMN player_id INTEGER")

    conn.commit()
    conn.close()


def load_from_db():
    """Load data from database into session state (once per session)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        players_df = pd.read_sql_query(
            '''
            SELECT id as "_id", team as "Team", spieler as "Spieler",
                   geschlecht as "Geschlecht",
                   v1 as "V1", v2 as "V2", v3 as "V3", v4 as "V4", v5 as "V5",
                   v6 as "V6", v7 as "V7", v8 as "V8", v9 as "V9", v10 as "V10",
                   a1 as "A1", a2 as "A2", a3 as "A3", a4 as "A4", a5 as "A5",
                   a6 as "A6", a7 as "A7", a8 as "A8", a9 as "A9", a10 as "A10"
            FROM players
            ORDER BY id
            ''',
            conn,
        )
        if not players_df.empty:
            st.session_state.players = players_df

        ko_df = pd.read_sql_query(
            '''
            SELECT id as "_id", runde as "Runde", team as "Team",
                   spieler as "Spieler", player_id as "PlayerID",
                   v1 as "V1", v2 as "V2", v3 as "V3", v4 as "V4", v5 as "V5",
                   v6 as "V6", v7 as "V7", v8 as "V8", v9 as "V9", v10 as "V10",
                   a1 as "A1", a2 as "A2", a3 as "A3", a4 as "A4", a5 as "A5",
                   a6 as "A6", a7 as "A7", a8 as "A8", a9 as "A9", a10 as "A10"
            FROM ko_data
            ORDER BY id
            ''',
            conn,
        )
        if not ko_df.empty:
            st.session_state.ko_data = ko_df
    finally:
        conn.close()


def _score_values(row):
    return [int(row[column]) for column in SCORE_COLS]


def _delete_stale(cursor, table, keep_ids):
    if keep_ids:
        placeholders = ",".join("?" for _ in keep_ids)
        cursor.execute(
            f"DELETE FROM {table} WHERE id NOT IN ({placeholders})", keep_ids
        )
    else:
        cursor.execute(f"DELETE FROM {table}")


def _save_players(conn, df):
    if "_id" not in df.columns:
        df["_id"] = None

    keep_ids = []
    for idx, row in df.iterrows():
        values = [
            row["Team"],
            row["Spieler"],
            row["Geschlecht"],
            *_score_values(row),
        ]
        row_id = row["_id"]
        if pd.isna(row_id):
            conn.execute(
                """
                INSERT INTO players (team, spieler, geschlecht,
                    v1, v2, v3, v4, v5, v6, v7, v8, v9, v10,
                    a1, a2, a3, a4, a5, a6, a7, a8, a9, a10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            df.at[idx, "_id"] = row_id
        else:
            row_id = int(row_id)
            conn.execute(
                """
                UPDATE players SET team = ?, spieler = ?, geschlecht = ?,
                    v1 = ?, v2 = ?, v3 = ?, v4 = ?, v5 = ?, v6 = ?,
                    v7 = ?, v8 = ?, v9 = ?, v10 = ?,
                    a1 = ?, a2 = ?, a3 = ?, a4 = ?, a5 = ?, a6 = ?,
                    a7 = ?, a8 = ?, a9 = ?, a10 = ?
                WHERE id = ?
                """,
                [*values, row_id],
            )
        keep_ids.append(row_id)

    _delete_stale(conn, "players", keep_ids)


def _save_ko(conn, df):
    if "_id" not in df.columns:
        df["_id"] = None
    if "PlayerID" not in df.columns:
        df["PlayerID"] = None

    keep_ids = []
    for idx, row in df.iterrows():
        player_id = row["PlayerID"]
        values = [
            row["Runde"],
            row["Team"],
            row["Spieler"],
            None if pd.isna(player_id) else int(player_id),
            *_score_values(row),
        ]
        row_id = row["_id"]
        if pd.isna(row_id):
            conn.execute(
                """
                INSERT INTO ko_data (runde, team, spieler, player_id,
                    v1, v2, v3, v4, v5, v6, v7, v8, v9, v10,
                    a1, a2, a3, a4, a5, a6, a7, a8, a9, a10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            df.at[idx, "_id"] = row_id
        else:
            row_id = int(row_id)
            conn.execute(
                """
                UPDATE ko_data SET runde = ?, team = ?, spieler = ?,
                    player_id = ?, v1 = ?, v2 = ?, v3 = ?, v4 = ?, v5 = ?,
                    v6 = ?, v7 = ?, v8 = ?, v9 = ?, v10 = ?,
                    a1 = ?, a2 = ?, a3 = ?, a4 = ?, a5 = ?, a6 = ?,
                    a7 = ?, a8 = ?, a9 = ?, a10 = ?
                WHERE id = ?
                """,
                [*values, row_id],
            )
        keep_ids.append(row_id)

    _delete_stale(conn, "ko_data", keep_ids)


def save_to_db():
    """Save current session state data to the database in one transaction."""
    has_players = "players" in st.session_state
    has_ko = "ko_data" in st.session_state
    if not has_players and not has_ko:
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            if has_players:
                _save_players(conn, st.session_state.players)
            if has_ko:
                _save_ko(conn, st.session_state.ko_data)
    finally:
        conn.close()


def reset_tournament():
    """Reset tournament data for a fresh start."""
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.execute("DELETE FROM players")
            conn.execute("DELETE FROM ko_data")
            conn.execute("DELETE FROM tournaments")
    finally:
        conn.close()

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    init_players()
    save_to_db()
