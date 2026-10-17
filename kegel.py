# Streamlit App for a bowling tournament
# Start with: streamlit run kegel.py

import streamlit as st
import pandas as pd
from datetime import datetime

from functions import (
    init_players,
    save_to_excel,
    create_excel_download,
    update_player_name,
    update_geschlecht,
    calculate_totals,
    get_team_scores,
    init_database,
    load_from_db,
    save_to_db,
    reset_tournament
)

st.set_page_config(page_title="Kegelturnier", layout="wide")

st.title("🎳 Kegelturnier – Live Auswertung")

# Initialize database
init_database()

# Load data from database if available
load_from_db()

# Initialize player data (only if not loaded from DB)
init_players()

# Clean up old team_bahn2 widget keys on startup
if "widgets_cleaned" not in st.session_state:
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith("team_bahn2_")]
    for key in keys_to_remove:
        del st.session_state[key]
    st.session_state.widgets_cleaned = True


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
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with col_save3:
    if st.button("🔄 Neues Turnier", type="primary", help="Alle Daten zurücksetzen und neu starten"):
        reset_tournament()
        st.success("✅ Turnier zurückgesetzt!")
        st.rerun()

st.markdown("---")

# Tabs for better overview
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🎳 Vorrunde", "🥊 Halbfinale", "🏆 Finale", "📊 Auswertung", "⚙️ Teams bearbeiten"])

with tab1:
    st.header("📝 Vorrunde - Eingabe")
    st.info("🎳 Parallel-Eingabe für 2 Bahnen - Wähle je ein Team pro Bahn aus")

    # Team selection for both lanes (sorted numerically)
    teams = sorted(st.session_state.players["Team"].unique(),
                   key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 999)

    # Determine default indices based on last edited team
    default_idx_1 = 0
    default_idx_2 = min(1, len(teams) - 1)

    if "last_edited_team" in st.session_state and st.session_state.last_edited_team in teams:
        last_idx = teams.index(st.session_state.last_edited_team)
        # Keep the last edited team selected on lane 1
        default_idx_1 = last_idx

        # For lane 2: find the next available team that's NOT the edited team
        # Start from the beginning and skip the edited team
        if len(teams) > 1:
            # Try to select the team right after position 0 (which would be Team 2 originally)
            candidate_idx = 0 if last_idx != 0 else 1
            default_idx_2 = candidate_idx
        else:
            default_idx_2 = last_idx

    col_select1, col_select2 = st.columns(2)
    with col_select1:
        st.markdown("### 🎯 Bahn 1")
        selected_team_1 = st.selectbox(
            "Team auswählen:", teams, index=default_idx_1, key="team_bahn1")
    with col_select2:
        st.markdown("### 🎯 Bahn 2")
        # Filter out team 1 from team 2 options to prevent same team on both lanes
        teams_lane2 = [t for t in teams if t != selected_team_1]
        if not teams_lane2:  # If only one team exists, allow it
            teams_lane2 = teams

        # Calculate correct index for filtered list
        if "last_edited_team" in st.session_state and st.session_state.last_edited_team in teams:
            # After editing, select next team in filtered list
            if default_idx_2 < len(teams) and teams[default_idx_2] in teams_lane2:
                default_idx_2_adjusted = teams_lane2.index(teams[default_idx_2])
            else:
                default_idx_2_adjusted = 0
        else:
            # Default: select Team 2 (index 0 in filtered list since Team 1 is removed)
            default_idx_2_adjusted = 0

        # Use dynamic key based on selected_team_1 to reset when lane 1 changes
        selected_team_2 = st.selectbox(
            "Team auswählen:", teams_lane2, index=default_idx_2_adjusted,
            key=f"team_bahn2_{selected_team_1.replace(' ', '_')}")

    st.markdown("---")

    # Display both teams side by side
    bahn1_col, bahn2_col = st.columns(2)

    # Lane 1 - Team 1
    with bahn1_col:
        st.markdown(f"### 🎳 Bahn 1: {selected_team_1}")
        team_data_1 = st.session_state.players[
            st.session_state.players["Team"] == selected_team_1
        ].copy()

        # First all VOLLE (full pins) for all players
        st.markdown("#### ⚪ VOLLE")
        for idx, row in team_data_1.iterrows():
            with st.expander(f"🎯 {row['Spieler']} - Volle", expanded=False):
                volle_cols = st.columns(5)
                volle_sum = 0
                for i in range(1, 11):
                    col_idx = (i - 1) % 5
                    with volle_cols[col_idx]:
                        val = st.number_input(
                            f"V{i}",
                            min_value=0,
                            max_value=9,
                            value=int(row[f"V{i}"]),
                            key=f"volle_b1_{idx}_{i}",
                            step=1
                        )
                        st.session_state.players.at[idx, f"V{i}"] = val
                        volle_sum += val
                st.metric("Summe Volle", volle_sum)

        st.markdown("---")

        # Then all ABRÄUMEN (spare attempts) for all players
        st.markdown("#### 🔴 ABRÄUMEN")
        for idx, row in team_data_1.iterrows():
            with st.expander(f"🎯 {row['Spieler']} - Abräumen", expanded=False):
                abr_cols = st.columns(5)
                abr_sum = 0
                for i in range(1, 11):
                    col_idx = (i - 1) % 5
                    with abr_cols[col_idx]:
                        val = st.number_input(
                            f"A{i}",
                            min_value=0,
                            max_value=9,
                            value=int(row[f"A{i}"]),
                            key=f"abr_b1_{idx}_{i}",
                            step=1
                        )
                        st.session_state.players.at[idx, f"A{i}"] = val
                        abr_sum += val
                st.metric("Summe Abräumen", abr_sum)

    # Lane 2 - Team 2
    with bahn2_col:
        st.markdown(f"### 🎳 Bahn 2: {selected_team_2}")
        team_data_2 = st.session_state.players[
            st.session_state.players["Team"] == selected_team_2
        ].copy()

        # First all VOLLE (full pins) for all players
        st.markdown("#### ⚪ VOLLE")
        for idx, row in team_data_2.iterrows():
            with st.expander(f"🎯 {row['Spieler']} - Volle", expanded=False):
                volle_cols = st.columns(5)
                volle_sum = 0
                for i in range(1, 11):
                    col_idx = (i - 1) % 5
                    with volle_cols[col_idx]:
                        val = st.number_input(
                            f"V{i}",
                            min_value=0,
                            max_value=9,
                            value=int(row[f"V{i}"]),
                            key=f"volle_b2_{idx}_{i}",
                            step=1
                        )
                        st.session_state.players.at[idx, f"V{i}"] = val
                        save_to_db()  # Auto-save to database
                        volle_sum += val
                st.metric("Summe Volle", volle_sum)

        st.markdown("---")

        # Then all ABRÄUMEN (spare attempts) for all players
        st.markdown("#### 🔴 ABRÄUMEN")
        for idx, row in team_data_2.iterrows():
            with st.expander(f"🎯 {row['Spieler']} - Abräumen", expanded=False):
                abr_cols = st.columns(5)
                abr_sum = 0
                for i in range(1, 11):
                    col_idx = (i - 1) % 5
                    with abr_cols[col_idx]:
                        val = st.number_input(
                            f"A{i}",
                            min_value=0,
                            max_value=9,
                            value=int(row[f"A{i}"]),
                            key=f"abr_b2_{idx}_{i}",
                            step=1
                        )
                        st.session_state.players.at[idx, f"A{i}"] = val
                        save_to_db()  # Auto-save to database
                        abr_sum += val
                st.metric("Summe Abräumen", abr_sum)

with tab2:
    st.header("🥊 Halbfinale")

    # Calculate totals
    df = st.session_state.players.copy()
    df = calculate_totals(df)
    team_scores = get_team_scores(df)

    if len(team_scores) >= 4:
        # Initialize KO data in session state
        if "ko_data" not in st.session_state:
            ko_data = []
            # For semifinals: 4 teams x 5 players
            for team_id in range(1, 5):
                for player_id in range(1, 6):
                    player_data = {
                        "Runde": "HF",
                        "Team": f"HF_Team_{team_id}",
                        "Spieler": f"Spieler {player_id}",
                    }
                    for i in range(1, 11):
                        player_data[f"V{i}"] = 0
                    for i in range(1, 11):
                        player_data[f"A{i}"] = 0
                    ko_data.append(player_data)
            # For finals: 2 teams x 5 players
            for team_id in range(1, 3):
                for player_id in range(1, 6):
                    player_data = {
                        "Runde": "Finale",
                        "Team": f"Finale_Team_{team_id}",
                        "Spieler": f"Spieler {player_id}",
                    }
                    for i in range(1, 11):
                        player_data[f"V{i}"] = 0
                    for i in range(1, 11):
                        player_data[f"A{i}"] = 0
                    ko_data.append(player_data)
            st.session_state.ko_data = pd.DataFrame(ko_data)

        top4 = team_scores.head(4).reset_index(drop=True)

        st.subheader("Top 4 Teams (nach Vorrunde)")
        col1, col2, col3, col4 = st.columns(4)

        for i, (idx, row) in enumerate(top4.iterrows()):
            col = [col1, col2, col3, col4][i]
            with col:
                st.metric(
                    label=f"{i+1}. Platz",
                    value=row["Team"],
                    delta=f"{int(row['Gesamt'])} Holz"
                )

        st.markdown("---")

        # Team selection for semifinals
        hf_teams = [top4.loc[0, 'Team'], top4.loc[1, 'Team'],
                    top4.loc[2, 'Team'], top4.loc[3, 'Team']]
        hf_team_mapping = {
            top4.loc[0, 'Team']: "HF_Team_1",
            top4.loc[1, 'Team']: "HF_Team_2",
            top4.loc[2, 'Team']: "HF_Team_3",
            top4.loc[3, 'Team']: "HF_Team_4"
        }

        # HALBFINALE 1: 1. vs 3.
        st.markdown("### 🔥 Halbfinale 1: 1. Platz vs 3. Platz")

        hf1_col1, hf1_col2 = st.columns(2)
        hf1_teams = [top4.loc[0, 'Team'], top4.loc[2, 'Team']]

        for hf_idx, (hf_col, team_name) in enumerate(zip([hf1_col1, hf1_col2], hf1_teams)):
            hf_team_key = f"HF_Team_{hf_idx + 1}"
            with hf_col:
                st.markdown(f"**🎳 Bahn {hf_idx + 1}: {team_name}** ({['1. Platz', '3. Platz'][hf_idx]})")
                with st.expander("🎯 Auf die Vollen", expanded=False):
                    # Get players from preliminary round
                    team_players = st.session_state.players[
                        st.session_state.players["Team"] == team_name
                    ]["Spieler"].tolist()

                    for p_idx, player in enumerate(team_players):
                        cols_v = st.columns([2] + [1]*5)
                        with cols_v[0]:
                            st.write(player)
                        for throw_idx in range(5):
                            with cols_v[throw_idx + 1]:
                                current_val = st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"V{throw_idx + 1}"
                                ].values
                                current_val = int(current_val[0]) if len(current_val) > 0 else 0

                                new_val = st.number_input(
                                    f"V{throw_idx + 1}",
                                    min_value=0,
                                    max_value=9,
                                    value=current_val,
                                    step=1,
                                    key=f"hf_{hf_team_key}_{player}_V{throw_idx + 1}",
                                    label_visibility="collapsed"
                                )
                                st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"V{throw_idx + 1}"
                                ] = new_val

                with st.expander("🎳 Abräumen", expanded=False):
                    for p_idx, player in enumerate(team_players):
                        cols_a = st.columns([2] + [1]*5)
                        with cols_a[0]:
                            st.write(player)
                        for throw_idx in range(5):
                            with cols_a[throw_idx + 1]:
                                current_val = st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"A{throw_idx + 1}"
                                ].values
                                current_val = int(current_val[0]) if len(current_val) > 0 else 0

                                new_val = st.number_input(
                                    f"A{throw_idx + 1}",
                                    min_value=0,
                                    max_value=9,
                                    value=current_val,
                                    step=1,
                                    key=f"hf_{hf_team_key}_{player}_A{throw_idx + 1}",
                                    label_visibility="collapsed"
                                )
                                st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"A{throw_idx + 1}"
                                ] = new_val

        st.markdown("---")

        # HALBFINALE 2: 2. vs 4.
        st.markdown("### 🔥 Halbfinale 2: 2. Platz vs 4. Platz")

        hf2_col1, hf2_col2 = st.columns(2)
        hf2_teams = [top4.loc[1, 'Team'], top4.loc[3, 'Team']]

        for hf_idx, (hf_col, team_name) in enumerate(zip([hf2_col1, hf2_col2], hf2_teams)):
            hf_team_key = f"HF_Team_{hf_idx + 3}"  # 3 and 4
            with hf_col:
                st.markdown(f"**🎳 Bahn {hf_idx + 1}: {team_name}** ({['2. Platz', '4. Platz'][hf_idx]})")
                with st.expander("🎯 Auf die Vollen", expanded=False):
                    # Get players from preliminary round
                    team_players = st.session_state.players[
                        st.session_state.players["Team"] == team_name
                    ]["Spieler"].tolist()

                    for p_idx, player in enumerate(team_players):
                        cols_v = st.columns([2] + [1]*5)
                        with cols_v[0]:
                            st.write(player)
                        for throw_idx in range(5):
                            with cols_v[throw_idx + 1]:
                                current_val = st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"V{throw_idx + 1}"
                                ].values
                                current_val = int(current_val[0]) if len(current_val) > 0 else 0

                                new_val = st.number_input(
                                    f"V{throw_idx + 1}",
                                    min_value=0,
                                    max_value=9,
                                    value=current_val,
                                    step=1,
                                    key=f"hf_{hf_team_key}_{player}_V{throw_idx + 1}",
                                    label_visibility="collapsed"
                                )
                                st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"V{throw_idx + 1}"
                                ] = new_val

                with st.expander("🎳 Abräumen", expanded=False):
                    for p_idx, player in enumerate(team_players):
                        cols_a = st.columns([2] + [1]*5)
                        with cols_a[0]:
                            st.write(player)
                        for throw_idx in range(5):
                            with cols_a[throw_idx + 1]:
                                current_val = st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"A{throw_idx + 1}"
                                ].values
                                current_val = int(current_val[0]) if len(current_val) > 0 else 0

                                new_val = st.number_input(
                                    f"A{throw_idx + 1}",
                                    min_value=0,
                                    max_value=9,
                                    value=current_val,
                                    step=1,
                                    key=f"hf_{hf_team_key}_{player}_A{throw_idx + 1}",
                                    label_visibility="collapsed"
                                )
                                st.session_state.ko_data.loc[
                                    (st.session_state.ko_data["Team"] == hf_team_key) &
                                    (st.session_state.ko_data["Spieler"] == player),
                                    f"A{throw_idx + 1}"
                                ] = new_val
    else:
        st.warning("Noch keine Top 4 Teams vorhanden!")

with tab3:
    st.header("🏆 Finale")

    # Calculate semifinal results
    if "ko_data" in st.session_state and not st.session_state.ko_data.empty:
        ko_df = st.session_state.ko_data.copy()
        ko_df = calculate_totals(ko_df)

        # Group by teams and sum
        hf_results = ko_df.groupby("Team").agg({
            "Volle": "sum",
            "Abräumen": "sum",
            "Gesamt": "sum"
        }).reset_index()

        # HF1 Gewinner (Team 1 vs Team 2)
        hf1_teams = hf_results[hf_results["Team"].isin(["HF_Team_1", "HF_Team_2"])]
        if len(hf1_teams) == 2:
            hf1_winner = hf1_teams.loc[hf1_teams["Gesamt"].idxmax(), "Team"]
        else:
            hf1_winner = None

        # HF2 Gewinner (Team 3 vs Team 4)
        hf2_teams = hf_results[hf_results["Team"].isin(["HF_Team_3", "HF_Team_4"])]
        if len(hf2_teams) == 2:
            hf2_winner = hf2_teams.loc[hf2_teams["Gesamt"].idxmax(), "Team"]
        else:
            hf2_winner = None

        if hf1_winner and hf2_winner:
            st.info(f"🥊 Gewinner HF1: {hf1_winner} vs Gewinner HF2: {hf2_winner}")

            # Finals input
            finale_col1, finale_col2 = st.columns(2)
            finale_teams = [hf1_winner, hf2_winner]

            for finale_idx, (finale_col, hf_team_key) in enumerate(zip([finale_col1, finale_col2], finale_teams)):
                finale_team_key = f"Finale_Team_{finale_idx + 1}"
                original_team_name = "Gewinner " + ("HF1" if finale_idx == 0 else "HF2")

                with finale_col:
                    st.markdown(f"**🏆 Bahn {finale_idx + 1}: {original_team_name}**")
                    with st.expander("🎯 Auf die Vollen", expanded=False):
                        # Get players from SF team
                        hf_players = st.session_state.ko_data[
                            st.session_state.ko_data["Team"] == hf_team_key
                        ]["Spieler"].tolist()

                        for p_idx, player in enumerate(hf_players):
                            cols_v = st.columns([2] + [1]*5)
                            with cols_v[0]:
                                st.write(player)
                            for throw_idx in range(5):
                                with cols_v[throw_idx + 1]:
                                    current_val = st.session_state.ko_data.loc[
                                        (st.session_state.ko_data["Team"] == finale_team_key) &
                                        (st.session_state.ko_data["Spieler"] == player),
                                        f"V{throw_idx + 1}"
                                    ].values
                                    current_val = int(current_val[0]) if len(current_val) > 0 else 0

                                    new_val = st.number_input(
                                        f"V{throw_idx + 1}",
                                        min_value=0,
                                        max_value=9,
                                        value=current_val,
                                        step=1,
                                        key=f"finale_{finale_team_key}_{player}_V{throw_idx + 1}",
                                        label_visibility="collapsed"
                                    )
                                    st.session_state.ko_data.loc[
                                        (st.session_state.ko_data["Team"] == finale_team_key) &
                                        (st.session_state.ko_data["Spieler"] == player),
                                        f"V{throw_idx + 1}"
                                    ] = new_val

                    with st.expander("🎳 Abräumen", expanded=False):
                        for p_idx, player in enumerate(hf_players):
                            cols_a = st.columns([2] + [1]*5)
                            with cols_a[0]:
                                st.write(player)
                            for throw_idx in range(5):
                                with cols_a[throw_idx + 1]:
                                    current_val = st.session_state.ko_data.loc[
                                        (st.session_state.ko_data["Team"] == finale_team_key) &
                                        (st.session_state.ko_data["Spieler"] == player),
                                        f"A{throw_idx + 1}"
                                    ].values
                                    current_val = int(current_val[0]) if len(current_val) > 0 else 0

                                    new_val = st.number_input(
                                        f"A{throw_idx + 1}",
                                        min_value=0,
                                        max_value=9,
                                        value=current_val,
                                        step=1,
                                        key=f"finale_{finale_team_key}_{player}_A{throw_idx + 1}",
                                        label_visibility="collapsed"
                                    )
                                    st.session_state.ko_data.loc[
                                        (st.session_state.ko_data["Team"] == finale_team_key) &
                                        (st.session_state.ko_data["Spieler"] == player),
                                        f"A{throw_idx + 1}"
                                    ] = new_val
        else:
            st.info("⏳ Bitte zuerst die Halbfinale abschließen")
    else:
        st.info("⏳ Noch keine Daten vorhanden")

with tab4:
    st.header("📊 Auswertung")

    # Calculate totals
    df = st.session_state.players.copy()
    df = calculate_totals(df)
    team_scores = get_team_scores(df)

    # Top 4 places of the tournament
    st.subheader("🏅 Turnier-Platzierung")
    if len(team_scores) >= 4:
        top4 = team_scores.head(4)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "🥇 1. Platz",
                top4.iloc[0]['Team'],
                f"{int(top4.iloc[0]['Gesamt'])} Holz",
                help=f"Volle: {int(top4.iloc[0]['Volle'])} | Abräumen: {int(top4.iloc[0]['Abräumen'])}"
            )

        with col2:
            st.metric(
                "🥈 2. Platz",
                top4.iloc[1]['Team'],
                f"{int(top4.iloc[1]['Gesamt'])} Holz",
                help=f"Volle: {int(top4.iloc[1]['Volle'])} | Abräumen: {int(top4.iloc[1]['Abräumen'])}"
            )

        with col3:
            st.metric(
                "🥉 3. Platz",
                top4.iloc[2]['Team'],
                f"{int(top4.iloc[2]['Gesamt'])} Holz",
                help=f"Volle: {int(top4.iloc[2]['Volle'])} | Abräumen: {int(top4.iloc[2]['Abräumen'])}"
            )

        with col4:
            st.metric(
                "4️⃣ 4. Platz",
                top4.iloc[3]['Team'],
                f"{int(top4.iloc[3]['Gesamt'])} Holz",
                help=f"Volle: {int(top4.iloc[3]['Volle'])} | Abräumen: {int(top4.iloc[3]['Abräumen'])}"
            )

    st.markdown("---")

    # Team ranking (preliminary round)
    st.subheader("🏆 Teamwertung (Vorrunde)")
    st.dataframe(team_scores, width='stretch')

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
                help=f"{best_player['Team']} - {int(best_player['Volle'])} Volle + {int(best_player['Abräumen'])} Abräumen"
            )

    with col2:
        best_female_data = df[df["Geschlecht"] == "w"]
        if not best_female_data.empty and best_female_data["Gesamt"].max() > 0:
            best_woman = best_female_data.loc[best_female_data["Gesamt"].idxmax()]
            st.metric(
                "👩 Beste Frau",
                best_woman["Spieler"],
                f"{int(best_woman['Gesamt'])} Holz",
                help=f"{best_woman['Team']} - {int(best_woman['Volle'])} Volle + {int(best_woman['Abräumen'])} Abräumen"
            )

    with col3:
        if not df.empty and df["Volle"].max() > 0:
            best_volle = df.loc[df["Volle"].idxmax()]
            st.metric(
                "🎯 Beste Volle",
                best_volle["Spieler"],
                f"{int(best_volle['Volle'])} Holz",
                help=f"{best_volle['Team']}"
            )

    st.markdown("---")

    # Top 10 Spieler gesamt
    st.subheader("🥇 Top 10 Spieler (Gesamt)")
    top_players = df.sort_values("Gesamt", ascending=False).head(10)[
        ["Spieler", "Team", "Geschlecht", "Volle", "Abräumen", "Gesamt"]
    ].reset_index(drop=True)
    top_players.index = top_players.index + 1
    top_players.index.name = "Rang"
    st.dataframe(top_players, width='stretch')

    st.caption("💡 Live-Auswertung – Änderungen werden sofort übernommen")

with tab5:
    st.info("📝 Hier kannst du Team- und Spielernamen anpassen")

    # Number of teams configuration
    st.markdown("### ⚙️ Anzahl der Teams")
    current_team_count = len(st.session_state.players["Team"].unique())

    col_teams, col_apply = st.columns([3, 1])
    with col_teams:
        new_team_count = st.number_input(
            "Wie viele Teams nehmen teil?",
            min_value=2,
            max_value=20,
            value=current_team_count,
            step=1,
            key="team_count_input"
        )
    with col_apply:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Anwenden", type="secondary"):
            if new_team_count != current_team_count:
                # Add or remove teams
                if new_team_count > current_team_count:
                    # Add new teams
                    for team_id in range(current_team_count + 1, new_team_count + 1):
                        for player_id in range(1, 6):
                            new_row = {
                                "Team": f"Team {team_id}",
                                "Spieler": f"Spieler {player_id}",
                                "Geschlecht": "m"
                            }
                            for i in range(1, 11):
                                new_row[f"V{i}"] = 0
                                new_row[f"A{i}"] = 0
                            st.session_state.players = pd.concat([
                                st.session_state.players,
                                pd.DataFrame([new_row])
                            ], ignore_index=True)
                else:
                    # Remove teams
                    teams_to_keep = [f"Team {i}" for i in range(1, new_team_count + 1)]
                    st.session_state.players = st.session_state.players[
                        st.session_state.players["Team"].isin(teams_to_keep)
                    ].reset_index(drop=True)

                save_to_db()
                st.success(f"✅ Teamanzahl auf {new_team_count} angepasst!")
                st.rerun()

    st.markdown("---")

    # Team selection (numerically sorted)
    teams = sorted(st.session_state.players["Team"].unique(),
                   key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 999)

    # Determine the preselected index
    default_index = 0
    if "last_edited_team" in st.session_state and st.session_state.last_edited_team in teams:
        default_index = teams.index(st.session_state.last_edited_team)

    selected_team_edit = st.selectbox(
        "Team zum Bearbeiten auswählen:", teams, index=default_index, key="edit_team_select")

    # Edit team name
    st.markdown("### Team umbenennen")
    col1, col2 = st.columns([3, 1])
    with col1:
        # Use dynamic key based on selected team to force reset when team changes
        new_team_name = st.text_input(
            "Neuer Teamname:",
            placeholder=selected_team_edit,
            key=f"team_rename_input_{selected_team_edit.replace(' ', '_')}"
        )
    with col2:
        if st.button("Team umbenennen", type="primary"):
            if new_team_name and new_team_name != selected_team_edit:
                st.session_state.players.loc[
                    st.session_state.players["Team"] == selected_team_edit, "Team"
                ] = new_team_name
                save_to_db()  # Save to database

                # Set last_edited_team to the new name so default logic will select it
                st.session_state.last_edited_team = new_team_name

                # Clear team selection widgets to reset with new team name
                if "team_bahn1" in st.session_state:
                    del st.session_state.team_bahn1

                # Clear all team_bahn2 variants to force reset on next render
                keys_to_remove = [k for k in st.session_state.keys() if k.startswith("team_bahn2_")]
                for k in keys_to_remove:
                    del st.session_state[k]

                # Clear all rename input fields
                rename_keys = [k for k in st.session_state.keys() if k.startswith("team_rename_input_")]
                for k in rename_keys:
                    del st.session_state[k]

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
                value=row['Spieler'],
                key=f"player_name_{selected_team_edit}_{idx}",
                placeholder="Namen eingeben",
                on_change=update_player_name,
                args=(idx, selected_team_edit)
            )
        with col2:
            st.selectbox(
                "m/w",
                options=["m", "w"],
                index=0 if row["Geschlecht"] == "m" else 1,
                key=f"geschlecht_edit_{selected_team_edit}_{idx}",
                label_visibility="collapsed",
                on_change=update_geschlecht,
                args=(idx, selected_team_edit)
            )
