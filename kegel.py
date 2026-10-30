# Streamlit App for a bowling tournament
# Start with: streamlit run kegel.py

from datetime import datetime

import streamlit as st

from functions import (
    calculate_totals,
    create_excel_download,
    empty_ko_df,
    get_player_ranking,
    get_team_scores,
    init_database,
    init_players,
    ko_player_mask,
    load_from_db,
    reset_tournament,
    resize_teams,
    save_to_db,
    save_to_excel,
    sorted_teams,
    sync_ko_round,
    team_player_entries,
    update_geschlecht,
    update_player_name,
)

st.set_page_config(page_title="Kegelturnier", layout="wide")

st.title("🎳 Kegelturnier – Live Auswertung")

# Initialize database and load persisted data once per session.
init_database()
if "players" not in st.session_state:
    load_from_db()
init_players()
if "ko_data" not in st.session_state:
    st.session_state.ko_data = empty_ko_df()

# Bumping this counter changes all score widget keys, which cleanly resets
# widget state after structural changes (team count / team renames).
st.session_state.setdefault("widget_generation", 0)

# On a fresh start the rows have no database id yet. Persist them before the
# KO slots are built so that KO rows can reference stable player ids.
if st.session_state.players["_id"].isna().any():
    save_to_db()


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def render_lane_inputs(team_name, lane):
    """Render the Volle/Abräumen inputs for one team on one lane."""
    generation = st.session_state.widget_generation
    team_data = st.session_state.players[
        st.session_state.players["Team"] == team_name
    ]

    for title, prefix, key_prefix in (
        ("⚪ VOLLE", "V", "volle"),
        ("🔴 ABRÄUMEN", "A", "abr"),
    ):
        st.markdown(f"#### {title}")
        for idx, row in team_data.iterrows():
            label = "Volle" if prefix == "V" else "Abräumen"
            with st.expander(f"🎯 {row['Spieler']} - {label}", expanded=False):
                columns = st.columns(5)
                total = 0
                for i in range(1, 11):
                    with columns[(i - 1) % 5]:
                        value = st.number_input(
                            f"{prefix}{i}",
                            min_value=0,
                            max_value=9,
                            value=int(row[f"{prefix}{i}"]),
                            key=f"{key_prefix}_{lane}_{generation}_{idx}_{i}",
                            step=1,
                        )
                        st.session_state.players.at[idx, f"{prefix}{i}"] = value
                        total += value
                st.metric(f"Summe {label}", total)


def render_ko_inputs(runde, team_key, team_name, key_prefix):
    """Render the KO inputs for one slot (semifinal or final)."""
    generation = st.session_state.widget_generation
    team_players = st.session_state.players[
        st.session_state.players["Team"] == team_name
    ]

    for expander_label, prefix in (
        ("🎯 Auf die Vollen", "V"),
        ("🎳 Abräumen", "A"),
    ):
        with st.expander(expander_label, expanded=False):
            for _, player_row in team_players.iterrows():
                player_name = player_row["Spieler"]
                player_id = player_row["_id"]

                columns = st.columns([2] + [1] * 5)
                with columns[0]:
                    st.write(player_name)

                for throw_idx in range(5):
                    column = f"{prefix}{throw_idx + 1}"
                    mask = ko_player_mask(
                        st.session_state.ko_data,
                        runde,
                        team_key,
                        player_id,
                        player_name,
                    )
                    current = (
                        int(st.session_state.ko_data.loc[mask, column].values[0])
                        if mask.any()
                        else 0
                    )
                    with columns[throw_idx + 1]:
                        new_value = st.number_input(
                            column,
                            min_value=0,
                            max_value=9,
                            value=current,
                            step=1,
                            key=f"{key_prefix}_{generation}_{player_name}_{column}",
                            label_visibility="collapsed",
                        )
                    st.session_state.ko_data.loc[mask, column] = new_value


def hf_slot_teams(team_scores):
    """Map semifinal slot keys to the actual team names (1v3, 2v4)."""
    if len(team_scores) < 4:
        return {}
    top4 = team_scores.head(4).reset_index(drop=True)
    return {
        "HF_Team_1": top4.loc[0, "Team"],
        "HF_Team_2": top4.loc[2, "Team"],
        "HF_Team_3": top4.loc[1, "Team"],
        "HF_Team_4": top4.loc[3, "Team"],
    }


def ko_winner(hf_results, team_keys):
    """Return the winner key of a semifinal, with a deterministic tie-break."""
    contenders = hf_results[hf_results["Team"].isin(team_keys)]
    if len(contenders) != 2:
        return None
    contenders = contenders.sort_values(
        ["Gesamt", "Abräumen", "Volle"], ascending=False
    )
    return contenders.iloc[0]["Team"]


# -----------------------------
# Input
# -----------------------------
st.header("✍️ Eingabe Spielergebnisse")

# Save buttons and reset at the top
col_save1, col_save2, col_save3, col_save4 = st.columns([2, 2, 2, 4])
with col_save1:
    if st.button("💾 Lokal Speichern", type="secondary"):
        try:
            save_to_db()  # Save to database
            filename = save_to_excel()
            st.success(f"✅ Gespeichert als: {filename}")
        except Exception as e:
            st.error(f"❌ Fehler beim Speichern: {e}")

with col_save2:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_data = create_excel_download()
    st.download_button(
        label="📥 Excel Download",
        data=excel_data,
        file_name=f"kegelturnier_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with col_save3:
    if st.button(
        "🔄 Neues Turnier",
        type="primary",
        help="Alle Daten zurücksetzen und neu starten",
    ):
        reset_tournament()
        st.success("✅ Turnier zurückgesetzt!")
        st.rerun()

st.markdown("---")

# Tabs for better overview
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🎳 Vorrunde", "🥊 Halbfinale", "🏆 Finale", "📊 Auswertung", "⚙️ Teams bearbeiten"]
)

with tab1:
    st.header("📝 Vorrunde - Eingabe")
    st.info(
        "🎳 Parallel-Eingabe für 2 Bahnen - Wähle je ein Team pro Bahn aus"
    )

    teams = sorted_teams(st.session_state.players)

    # Keep the last edited team selected on lane 1.
    default_idx_1 = 0
    if (
        "last_edited_team" in st.session_state
        and st.session_state.last_edited_team in teams
    ):
        default_idx_1 = teams.index(st.session_state.last_edited_team)

    generation = st.session_state.widget_generation
    col_select1, col_select2 = st.columns(2)
    with col_select1:
        st.markdown("### 🎯 Bahn 1")
        selected_team_1 = st.selectbox(
            "Team auswählen:",
            teams,
            index=default_idx_1,
            key=f"team_bahn1_{generation}",
        )
    with col_select2:
        st.markdown("### 🎯 Bahn 2")
        teams_lane2 = [t for t in teams if t != selected_team_1] or teams

        # Default: the team that follows the lane 1 team in the list.
        default_idx_2 = 0
        if len(teams) > 1:
            next_team = teams[(teams.index(selected_team_1) + 1) % len(teams)]
            if next_team in teams_lane2:
                default_idx_2 = teams_lane2.index(next_team)

        selected_team_2 = st.selectbox(
            "Team auswählen:",
            teams_lane2,
            index=default_idx_2,
            key=(
                f"team_bahn2_{generation}_"
                f"{selected_team_1.replace(' ', '_')}"
            ),
        )

    st.markdown("---")

    # Display both teams side by side
    bahn1_col, bahn2_col = st.columns(2)

    with bahn1_col:
        st.markdown(f"### 🎳 Bahn 1: {selected_team_1}")
        render_lane_inputs(selected_team_1, "b1")

    with bahn2_col:
        st.markdown(f"### 🎳 Bahn 2: {selected_team_2}")
        render_lane_inputs(selected_team_2, "b2")

with tab2:
    st.header("🥊 Halbfinale")

    df = calculate_totals(st.session_state.players.copy())
    team_scores = get_team_scores(df)

    if len(team_scores) >= 4:
        slot_teams = hf_slot_teams(team_scores)

        assignments = {
            team_key: team_player_entries(st.session_state.players, team_name)
            for team_key, team_name in slot_teams.items()
        }
        st.session_state.ko_data = sync_ko_round(
            st.session_state.ko_data, "HF", assignments
        )

        st.subheader("Top 4 Teams (nach Vorrunde)")
        col1, col2, col3, col4 = st.columns(4)
        for i, (_, row) in enumerate(team_scores.head(4).iterrows()):
            with [col1, col2, col3, col4][i]:
                st.metric(
                    label=f"{i + 1}. Platz",
                    value=row["Team"],
                    delta=f"{int(row['Gesamt'])} Holz",
                )

        st.markdown("---")

        st.markdown("### 🔥 Halbfinale 1: 1. Platz vs 3. Platz")
        hf1_col1, hf1_col2 = st.columns(2)
        for hf_col, team_key, rank_label in zip(
            [hf1_col1, hf1_col2],
            ["HF_Team_1", "HF_Team_2"],
            ["1. Platz", "3. Platz"],
        ):
            team_name = slot_teams[team_key]
            with hf_col:
                st.markdown(f"**🎳 {team_name}** ({rank_label})")
                render_ko_inputs("HF", team_key, team_name, f"hf_{team_key}")

        st.markdown("---")

        st.markdown("### 🔥 Halbfinale 2: 2. Platz vs 4. Platz")
        hf2_col1, hf2_col2 = st.columns(2)
        for hf_col, team_key, rank_label in zip(
            [hf2_col1, hf2_col2],
            ["HF_Team_3", "HF_Team_4"],
            ["2. Platz", "4. Platz"],
        ):
            team_name = slot_teams[team_key]
            with hf_col:
                st.markdown(f"**🎳 {team_name}** ({rank_label})")
                render_ko_inputs("HF", team_key, team_name, f"hf_{team_key}")
    else:
        st.warning("Noch keine Top 4 Teams vorhanden!")

with tab3:
    st.header("🏆 Finale")

    hf_rows = st.session_state.ko_data[
        st.session_state.ko_data["Runde"] == "HF"
    ]
    if hf_rows.empty:
        st.info("⏳ Bitte zuerst die Halbfinale abschließen")
    else:
        hf_df = calculate_totals(hf_rows.copy())
        hf_results = hf_df.groupby("Team").agg(
            {"Volle": "sum", "Abräumen": "sum", "Gesamt": "sum"}
        ).reset_index()

        hf1_winner = ko_winner(hf_results, ["HF_Team_1", "HF_Team_2"])
        hf2_winner = ko_winner(hf_results, ["HF_Team_3", "HF_Team_4"])

        slot_teams = hf_slot_teams(
            get_team_scores(calculate_totals(st.session_state.players.copy()))
        )

        winner_teams = [
            slot_teams.get(hf1_winner),
            slot_teams.get(hf2_winner),
        ]

        if all(winner_teams):
            assignments = {
                "Finale_Team_1": team_player_entries(
                    st.session_state.players, winner_teams[0]
                ),
                "Finale_Team_2": team_player_entries(
                    st.session_state.players, winner_teams[1]
                ),
            }
            st.session_state.ko_data = sync_ko_round(
                st.session_state.ko_data, "Finale", assignments
            )

            st.info(
                f"🥊 Finale: {winner_teams[0]} vs {winner_teams[1]}"
            )

            finale_col1, finale_col2 = st.columns(2)
            for finale_idx, (finale_col, team_name) in enumerate(
                zip([finale_col1, finale_col2], winner_teams)
            ):
                finale_team_key = f"Finale_Team_{finale_idx + 1}"
                with finale_col:
                    st.markdown(f"**🏆 Bahn {finale_idx + 1}: {team_name}**")
                    render_ko_inputs(
                        "Finale",
                        finale_team_key,
                        team_name,
                        f"finale_{finale_team_key}",
                    )
        else:
            st.info("⏳ Bitte zuerst die Halbfinale abschließen")

with tab4:
    st.header("📊 Auswertung")

    df = calculate_totals(st.session_state.players.copy())
    team_scores = get_team_scores(df)

    # Top 4 places of the tournament
    st.subheader("🏅 Turnier-Platzierung")
    if len(team_scores) >= 4:
        top4 = team_scores.head(4)
        col1, col2, col3, col4 = st.columns(4)

        medals = ["🥇 1. Platz", "🥈 2. Platz", "🥉 3. Platz", "4️⃣ 4. Platz"]
        for col, medal, (_, row) in zip(
            [col1, col2, col3, col4], medals, top4.iterrows()
        ):
            with col:
                st.metric(
                    medal,
                    row["Team"],
                    f"{int(row['Gesamt'])} Holz",
                    help=(
                        f"Volle: {int(row['Volle'])} | "
                        f"Abräumen: {int(row['Abräumen'])}"
                    ),
                )

    st.markdown("---")

    # Team ranking (preliminary round)
    st.subheader("🏆 Teamwertung (Vorrunde)")
    st.dataframe(team_scores, width="stretch")

    st.markdown("---")

    # Best results
    st.subheader("🏆 Beste Einzelergebnisse")
    col1, col2, col3 = st.columns(3)

    with col1:
        if not df.empty and df["Gesamt"].max() > 0:
            best_player = df.loc[df["Gesamt"].idxmax()]
            st.metric(
                "🏆 Bester Spieler",
                best_player["Spieler"],
                f"{int(best_player['Gesamt'])} Holz",
                help=(
                    f"{best_player['Team']} - {int(best_player['Volle'])} Volle "
                    f"+ {int(best_player['Abräumen'])} Abräumen"
                ),
            )

    with col2:
        best_female_data = df[df["Geschlecht"] == "w"]
        if not best_female_data.empty and best_female_data["Gesamt"].max() > 0:
            best_woman = best_female_data.loc[best_female_data["Gesamt"].idxmax()]
            st.metric(
                "👩 Beste Frau",
                best_woman["Spieler"],
                f"{int(best_woman['Gesamt'])} Holz",
                help=(
                    f"{best_woman['Team']} - {int(best_woman['Volle'])} Volle "
                    f"+ {int(best_woman['Abräumen'])} Abräumen"
                ),
            )

    with col3:
        if not df.empty and df["Volle"].max() > 0:
            best_volle = df.loc[df["Volle"].idxmax()]
            st.metric(
                "🎯 Beste Volle",
                best_volle["Spieler"],
                f"{int(best_volle['Volle'])} Holz",
                help=f"{best_volle['Team']}",
            )

    st.markdown("---")

    # Top 10 Spieler gesamt
    st.subheader("🥇 Top 10 Spieler (Gesamt)")
    st.dataframe(get_player_ranking(df, limit=10), width="stretch")

    st.caption("💡 Live-Auswertung – Änderungen werden sofort übernommen")

with tab5:
    st.info("📝 Hier kannst du Team- und Spielernamen anpassen")

    # Number of teams configuration
    st.markdown("### ⚙️ Anzahl der Teams")
    teams = sorted_teams(st.session_state.players)
    current_team_count = len(teams)

    col_teams, col_apply = st.columns([3, 1])
    with col_teams:
        new_team_count = st.number_input(
            "Wie viele Teams nehmen teil?",
            min_value=2,
            max_value=20,
            value=current_team_count,
            step=1,
            key="team_count_input",
        )
    with col_apply:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Anwenden", type="secondary"):
            if new_team_count != current_team_count:
                st.session_state.players = resize_teams(
                    st.session_state.players, int(new_team_count)
                )
                st.session_state.widget_generation += 1
                save_to_db()
                st.success(f"✅ Teamanzahl auf {new_team_count} angepasst!")
                st.rerun()

    st.markdown("---")

    # Determine the preselected index
    teams = sorted_teams(st.session_state.players)
    default_index = 0
    if (
        "last_edited_team" in st.session_state
        and st.session_state.last_edited_team in teams
    ):
        default_index = teams.index(st.session_state.last_edited_team)

    selected_team_edit = st.selectbox(
        "Team zum Bearbeiten auswählen:",
        teams,
        index=default_index,
        key=f"edit_team_select_{st.session_state.widget_generation}",
    )

    # Edit team name
    st.markdown("### Team umbenennen")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_team_name = st.text_input(
            "Neuer Teamname:",
            placeholder=selected_team_edit,
            key=f"team_rename_input_{selected_team_edit.replace(' ', '_')}",
        )
    with col2:
        if st.button("Team umbenennen", type="primary"):
            if new_team_name and new_team_name != selected_team_edit:
                st.session_state.players.loc[
                    st.session_state.players["Team"] == selected_team_edit,
                    "Team",
                ] = new_team_name
                st.session_state.last_edited_team = new_team_name
                st.session_state.widget_generation += 1
                save_to_db()

                st.success(f"Team umbenannt zu '{new_team_name}'")
                st.rerun()

    st.markdown("---")
    st.markdown("### Spielernamen und Geschlecht bearbeiten")

    # Players of the selected team
    team_players = st.session_state.players[
        st.session_state.players["Team"] == selected_team_edit
    ].copy()

    for idx, row in team_players.iterrows():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.text_input(
                "Spielername",
                value=row["Spieler"],
                key=f"player_name_{selected_team_edit}_{idx}",
                placeholder="Namen eingeben",
                on_change=update_player_name,
                args=(idx, selected_team_edit),
            )
        with col2:
            st.selectbox(
                "m/w",
                options=["m", "w"],
                index=0 if row["Geschlecht"] == "m" else 1,
                key=f"geschlecht_edit_{selected_team_edit}_{idx}",
                label_visibility="collapsed",
                on_change=update_geschlecht,
                args=(idx, selected_team_edit),
            )

# Persist all changes once per script run (one transaction instead of 20x).
save_to_db()
