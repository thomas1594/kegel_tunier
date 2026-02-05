"""
Helper functions for the bowling tournament app
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import sqlite3
import json
import os

# Database configuration
DB_DIR = os.getenv('DB_DIR', 'data')
DB_PATH = os.path.join(DB_DIR, 'kegelturnier.db')

# Ensure data directory exists
os.makedirs(DB_DIR, exist_ok=True)


def init_players():
    """Initialize player data with 10 throws per category."""
    if "players" not in st.session_state:
        data = []
        for team_id in range(1, 11):
            for player_id in range(1, 6):
                player_data = {
                    "Team": f"Team {team_id}",
                    "Spieler": f"Spieler {player_id}",
                    "Geschlecht": "m",
                }
                # 10 throws for "Volle"
                for i in range(1, 11):
                    player_data[f"V{i}"] = 0
                # 10 throws for "Abräumen"
                for i in range(1, 11):
                    player_data[f"A{i}"] = 0
                data.append(player_data)
        st.session_state.players = pd.DataFrame(data)


def save_to_excel():
    """Save all data to an Excel file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kegelturnier_{timestamp}.xlsx"

    # Calculate totals
    df_export = st.session_state.players.copy()
    volle_cols = [f"V{i}" for i in range(1, 11)]
    abr_cols = [f"A{i}" for i in range(1, 11)]
    df_export["Volle_Summe"] = df_export[volle_cols].sum(axis=1)
    df_export["Abräumen_Summe"] = df_export[abr_cols].sum(axis=1)
    df_export["Gesamt"] = df_export["Volle_Summe"] + df_export["Abräumen_Summe"]

    # Team evaluation
    team_scores = (
        df_export.groupby("Team")["Gesamt"]
        .sum()
        .reset_index()
        .sort_values("Gesamt", ascending=False)
        .reset_index(drop=True)
    )
    team_scores.index = team_scores.index + 1
    team_scores.index.name = "Platz"

    # Player ranking
    player_ranking = df_export.sort_values("Gesamt", ascending=False)[
        ["Spieler", "Team", "Geschlecht", "Volle_Summe", "Abräumen_Summe", "Gesamt"]
    ].reset_index(drop=True)
    player_ranking.index = player_ranking.index + 1
    player_ranking.index.name = "Rang"

    # Write to Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='Alle Würfe', index=False)
        team_scores.to_excel(writer, sheet_name='Team-Ranking')
        player_ranking.to_excel(writer, sheet_name='Spieler-Ranking')

    return filename


def create_excel_download():
    """Create Excel file for download."""
    df_export = st.session_state.players.copy()
    volle_cols = [f"V{i}" for i in range(1, 11)]
    abr_cols = [f"A{i}" for i in range(1, 11)]
    df_export["Volle_Summe"] = df_export[volle_cols].sum(axis=1)
    df_export["Abräumen_Summe"] = df_export[abr_cols].sum(axis=1)
    df_export["Gesamt"] = df_export["Volle_Summe"] + df_export["Abräumen_Summe"]

    # Team evaluation
    team_scores = (
        df_export.groupby("Team")["Gesamt"]
        .sum()
        .reset_index()
        .sort_values("Gesamt", ascending=False)
        .reset_index(drop=True)
    )
    team_scores.index = team_scores.index + 1
    team_scores.index.name = "Platz"

    # Player ranking
    player_ranking = df_export.sort_values("Gesamt", ascending=False)[
        ["Spieler", "Team", "Geschlecht", "Volle_Summe", "Abräumen_Summe", "Gesamt"]
    ].reset_index(drop=True)
    player_ranking.index = player_ranking.index + 1
    player_ranking.index.name = "Rang"

    # In-memory buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='Alle Würfe', index=False)
        team_scores.to_excel(writer, sheet_name='Team-Ranking')
        player_ranking.to_excel(writer, sheet_name='Spieler-Ranking')

    return buffer.getvalue()


def update_player_name(idx, team):
    """Callback function for automatically saving player name."""
    key = f"player_name_{team}_{idx}"
    if key not in st.session_state or "players" not in st.session_state:
        return  # Skip if session was reset
    new_name = st.session_state[key]
    st.session_state.players.at[idx, "Spieler"] = new_name
    st.session_state.last_edited_team = team
    save_to_db()  # Auto-save to database


def update_geschlecht(idx, team):
    """Callback function for automatically saving gender."""
    key = f"geschlecht_edit_{team}_{idx}"
    if key not in st.session_state or "players" not in st.session_state:
        return  # Skip if session was reset
    new_geschlecht = st.session_state[key]
    st.session_state.players.at[idx, "Geschlecht"] = new_geschlecht
    st.session_state.last_edited_team = team
    save_to_db()  # Auto-save to database


def calculate_totals(df):
    """Calculate total values for a DataFrame."""
    volle_cols = [f"V{i}" for i in range(1, 11)]
    abr_cols = [f"A{i}" for i in range(1, 11)]
    df["Volle"] = df[volle_cols].sum(axis=1)
    df["Abräumen"] = df[abr_cols].sum(axis=1)
    df["Gesamt"] = df["Volle"] + df["Abräumen"]
    return df


def get_team_scores(df):
    """Calculates team rankings."""
    team_scores = df.groupby("Team").agg({
        "Volle": "sum",
        "Abräumen": "sum",
        "Gesamt": "sum"
    }).reset_index()
    team_scores = team_scores.sort_values("Gesamt", ascending=False).reset_index(drop=True)
    team_scores.insert(0, "Rang", range(1, len(team_scores) + 1))
    return team_scores


# Database functions
def init_database():
    """Initialize SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create players table for preliminary round
    cursor.execute('''
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
    ''')

    # Create ko_data table for semifinals and finals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ko_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            runde TEXT NOT NULL,
            team TEXT NOT NULL,
            spieler TEXT NOT NULL,
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
    ''')

    # Create tournaments metadata table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived BOOLEAN DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()


def load_from_db():
    """Load data from database into session state."""
    conn = sqlite3.connect(DB_PATH)

    # Load players data
    players_df = pd.read_sql_query('''
        SELECT team as "Team", spieler as "Spieler", geschlecht as "Geschlecht",
               v1 as "V1", v2 as "V2", v3 as "V3", v4 as "V4", v5 as "V5",
               v6 as "V6", v7 as "V7", v8 as "V8", v9 as "V9", v10 as "V10",
               a1 as "A1", a2 as "A2", a3 as "A3", a4 as "A4", a5 as "A5",
               a6 as "A6", a7 as "A7", a8 as "A8", a9 as "A9", a10 as "A10"
        FROM players
        ORDER BY id
    ''', conn)

    if not players_df.empty:
        st.session_state.players = players_df

    # Load KO data
    ko_df = pd.read_sql_query('''
        SELECT runde as "Runde", team as "Team", spieler as "Spieler",
               v1 as "V1", v2 as "V2", v3 as "V3", v4 as "V4", v5 as "V5",
               v6 as "V6", v7 as "V7", v8 as "V8", v9 as "V9", v10 as "V10",
               a1 as "A1", a2 as "A2", a3 as "A3", a4 as "A4", a5 as "A5",
               a6 as "A6", a7 as "A7", a8 as "A8", a9 as "A9", a10 as "A10"
        FROM ko_data
        ORDER BY id
    ''', conn)

    if not ko_df.empty:
        st.session_state.ko_data = ko_df

    conn.close()


def save_to_db():
    """Save current session state data to database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute('DELETE FROM players')
    cursor.execute('DELETE FROM ko_data')

    # Save players data
    if "players" in st.session_state and not st.session_state.players.empty:
        df = st.session_state.players
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO players (team, spieler, geschlecht,
                    v1, v2, v3, v4, v5, v6, v7, v8, v9, v10,
                    a1, a2, a3, a4, a5, a6, a7, a8, a9, a10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['Team'], row['Spieler'], row['Geschlecht'],
                int(row['V1']), int(row['V2']), int(row['V3']), int(row['V4']), int(row['V5']),
                int(row['V6']), int(row['V7']), int(row['V8']), int(row['V9']), int(row['V10']),
                int(row['A1']), int(row['A2']), int(row['A3']), int(row['A4']), int(row['A5']),
                int(row['A6']), int(row['A7']), int(row['A8']), int(row['A9']), int(row['A10'])
            ))

    # Save KO data
    if "ko_data" in st.session_state and not st.session_state.ko_data.empty:
        df = st.session_state.ko_data
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO ko_data (runde, team, spieler,
                    v1, v2, v3, v4, v5, v6, v7, v8, v9, v10,
                    a1, a2, a3, a4, a5, a6, a7, a8, a9, a10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['Runde'], row['Team'], row['Spieler'],
                int(row['V1']), int(row['V2']), int(row['V3']), int(row['V4']), int(row['V5']),
                int(row['V6']), int(row['V7']), int(row['V8']), int(row['V9']), int(row['V10']),
                int(row['A1']), int(row['A2']), int(row['A3']), int(row['A4']), int(row['A5']),
                int(row['A6']), int(row['A7']), int(row['A8']), int(row['A9']), int(row['A10'])
            ))

    conn.commit()
    conn.close()


def reset_tournament():
    """Reset tournament data for a fresh start."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear all data
    cursor.execute('DELETE FROM players')
    cursor.execute('DELETE FROM ko_data')
    cursor.execute('DELETE FROM tournaments')

    conn.commit()
    conn.close()

    # Clear all session state to ensure clean reset
    keys_to_delete = list(st.session_state.keys())
    for key in keys_to_delete:
        del st.session_state[key]

    # Reinitialize with fresh data
    init_players()
    save_to_db()
