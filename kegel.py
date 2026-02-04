# Streamlit App für ein Kegelturnier
# Starten mit: streamlit run kegel.py

import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="Kegelturnier", layout="wide")

st.title("🎳 Kegelturnier – Live Auswertung")

# -----------------------------
# Initiale Datenstruktur
# -----------------------------


def init_players():
    """Initialisiert die Spielerdaten mit 10 Würfen pro Kategorie."""
    if "players" not in st.session_state:
        data = []
        for team_id in range(1, 11):
            for player_id in range(1, 6):
                player_data = {
                    "Team": f"Team {team_id}",
                    "Spieler": f"Spieler {player_id}",
                    "Geschlecht": "m",
                }
                # 10 Würfe für Volle
                for i in range(1, 11):
                    player_data[f"V{i}"] = 0
                # 10 Würfe für Abräumen
                for i in range(1, 11):
                    player_data[f"A{i}"] = 0
                data.append(player_data)
        st.session_state.players = pd.DataFrame(data)


init_players()

# -----------------------------
# Speichern & Laden Funktionen
# -----------------------------


def save_to_excel():
    """Speichert alle Daten in eine Excel-Datei."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kegelturnier_{timestamp}.xlsx"

    # Berechne Gesamtwerte
    df_export = st.session_state.players.copy()
    volle_cols = [f"V{i}" for i in range(1, 11)]
    abr_cols = [f"A{i}" for i in range(1, 11)]
    df_export["Volle_Summe"] = df_export[volle_cols].sum(axis=1)
    df_export["Abräumen_Summe"] = df_export[abr_cols].sum(axis=1)
    df_export["Gesamt"] = df_export["Volle_Summe"] + \
        df_export["Abräumen_Summe"]

    # Team-Auswertung
    team_scores = (
        df_export.groupby("Team")["Gesamt"]
        .sum()
        .reset_index()
        .sort_values("Gesamt", ascending=False)
        .reset_index(drop=True)
    )
    team_scores.index = team_scores.index + 1
    team_scores.index.name = "Platz"

    # Spieler-Ranking
    player_ranking = df_export.sort_values("Gesamt", ascending=False)[
        ["Spieler", "Team", "Geschlecht", "Volle_Summe", "Abräumen_Summe", "Gesamt"]
    ].reset_index(drop=True)
    player_ranking.index = player_ranking.index + 1
    player_ranking.index.name = "Rang"

    # In Excel schreiben
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='Alle Würfe', index=False)
        team_scores.to_excel(writer, sheet_name='Team-Ranking')
        player_ranking.to_excel(writer, sheet_name='Spieler-Ranking')

    return filename


def create_excel_download():
    """Erstellt Excel-Datei für Download."""
    df_export = st.session_state.players.copy()
    volle_cols = [f"V{i}" for i in range(1, 11)]
    abr_cols = [f"A{i}" for i in range(1, 11)]
    df_export["Volle_Summe"] = df_export[volle_cols].sum(axis=1)
    df_export["Abräumen_Summe"] = df_export[abr_cols].sum(axis=1)
    df_export["Gesamt"] = df_export["Volle_Summe"] + \
        df_export["Abräumen_Summe"]

    # Team-Auswertung
    team_scores = (
        df_export.groupby("Team")["Gesamt"]
        .sum()
        .reset_index()
        .sort_values("Gesamt", ascending=False)
        .reset_index(drop=True)
    )
    team_scores.index = team_scores.index + 1
    team_scores.index.name = "Platz"

    # Spieler-Ranking
    player_ranking = df_export.sort_values("Gesamt", ascending=False)[
        ["Spieler", "Team", "Geschlecht", "Volle_Summe", "Abräumen_Summe", "Gesamt"]
    ].reset_index(drop=True)
    player_ranking.index = player_ranking.index + 1
    player_ranking.index.name = "Rang"

    # In Memory Buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name='Alle Würfe', index=False)
        team_scores.to_excel(writer, sheet_name='Team-Ranking')
        player_ranking.to_excel(writer, sheet_name='Spieler-Ranking')

    return buffer.getvalue()


# -----------------------------
# Eingabe
# -----------------------------
st.header("✍️ Eingabe Spielergebnisse")

# Sicherungs-Buttons oben
col_save1, col_save2, col_save3 = st.columns([2, 2, 6])
with col_save1:
    if st.button("💾 Lokal Speichern", type="secondary"):
        try:
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

st.markdown("---")

# Tabs für bessere Übersicht
tab1, tab2, tab3 = st.tabs(
    ["📝 Eingabe nach Teams", "📊 Alle Daten", "⚙️ Namen bearbeiten"])

with tab1:
    st.info("🎳 Parallel-Eingabe für 2 Bahnen - Wähle je ein Team pro Bahn aus")

    # Team-Auswahl für beide Bahnen (numerisch sortiert)
    teams = sorted(st.session_state.players["Team"].unique(),
                   key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 999)

    col_select1, col_select2 = st.columns(2)
    with col_select1:
        st.markdown("### 🎯 Bahn 1")
        selected_team_1 = st.selectbox(
            "Team auswählen:", teams, key="team_bahn1")
    with col_select2:
        st.markdown("### 🎯 Bahn 2")
        # Versuche das nächste Team vorzuschlagen
        default_idx = min(1, len(teams) - 1)
        selected_team_2 = st.selectbox(
            "Team auswählen:", teams, index=default_idx, key="team_bahn2")

    st.markdown("---")

    # Beide Teams nebeneinander anzeigen
    bahn1_col, bahn2_col = st.columns(2)

    # Bahn 1 - Team 1
    with bahn1_col:
        st.markdown(f"### 🎳 Bahn 1: {selected_team_1}")
        team_data_1 = st.session_state.players[
            st.session_state.players["Team"] == selected_team_1
        ].copy()

        for idx, row in team_data_1.iterrows():
            with st.expander(f"🎯 {row['Spieler']}", expanded=False):
                # Geschlecht auswählen
                geschlecht = st.radio(
                    "Geschlecht:",
                    options=["m", "w"],
                    index=0 if row["Geschlecht"] == "m" else 1,
                    key=f"geschlecht_b1_{idx}",
                    horizontal=True
                )
                st.session_state.players.at[idx, "Geschlecht"] = geschlecht

                st.markdown("**Volle (10 Würfe)**")
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

                st.markdown("**Abräumen (10 Würfe)**")
                abr_cols = st.columns(5)
                abr_sum = 0
                for i in range(1, 11):
                    col_idx = (i - 1) % 5
                    with abr_cols[col_idx]:
                        val = st.number_input(
                            f"A{i}",
                            min_value=0,
                            max_value=9,
                            key=f"abr_b1_{idx}_{i}",
                            step=1
                        )
                        st.session_state.players.at[idx, f"A{i}"] = val
                        abr_sum += val
                st.metric("Summe Abräumen", abr_sum)
                st.success(f"**Gesamt: {volle_sum + abr_sum} Holz**")

    # Bahn 2 - Team 2
    with bahn2_col:
        st.markdown(f"### 🎳 Bahn 2: {selected_team_2}")
        team_data_2 = st.session_state.players[
            st.session_state.players["Team"] == selected_team_2
        ].copy()

        for idx, row in team_data_2.iterrows():
            with st.expander(f"🎯 {row['Spieler']}", expanded=False):
                # Geschlecht auswählen
                geschlecht = st.radio(
                    "Geschlecht:",
                    options=["m", "w"],
                    index=0 if row["Geschlecht"] == "m" else 1,
                    key=f"geschlecht_b2_{idx}",
                    horizontal=True
                )
                st.session_state.players.at[idx, "Geschlecht"] = geschlecht

                st.markdown("**Volle (10 Würfe)**")
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
                        volle_sum += val
                st.metric("Summe Volle", volle_sum)

                st.markdown("**Abräumen (10 Würfe)**")
                abr_cols = st.columns(5)
                abr_sum = 0
                for i in range(1, 11):
                    col_idx = (i - 1) % 5
                    with abr_cols[col_idx]:
                        val = st.number_input(
                            f"A{i}",
                            min_value=0,
                            max_value=9,
                            key=f"abr_b2_{idx}_{i}",
                            step=1
                        )
                        st.session_state.players.at[idx, f"A{i}"] = val
                        abr_sum += val
                st.metric("Summe Abräumen", abr_sum)
                st.success(f"**Gesamt: {volle_sum + abr_sum} Holz**")

with tab2:
    st.info("Übersicht aller eingegebenen Daten")
    st.dataframe(st.session_state.players, use_container_width=True)

with tab3:
    st.info("📝 Hier kannst du Team- und Spielernamen anpassen")

    # Team-Auswahl (numerisch sortiert)
    teams = sorted(st.session_state.players["Team"].unique(),
                   key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 999)
    selected_team_edit = st.selectbox(
        "Team zum Bearbeiten auswählen:", teams, key="edit_team_select")

    # Teamname bearbeiten
    st.markdown("### Team umbenennen")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_team_name = st.text_input(
            "Neuer Teamname:",
            value=selected_team_edit,
            key="new_team_name"
        )
    with col2:
        if st.button("Team umbenennen", type="primary"):
            if new_team_name and new_team_name != selected_team_edit:
                st.session_state.players.loc[
                    st.session_state.players["Team"] == selected_team_edit, "Team"
                ] = new_team_name
                st.success(f"Team umbenannt zu '{new_team_name}'")
                st.rerun()

    st.markdown("---")
    st.markdown("### Spielernamen und Geschlecht bearbeiten")

    # Spieler des ausgewählten Teams
    team_players = st.session_state.players[
        st.session_state.players["Team"] == selected_team_edit
    ].copy()

    for idx, row in team_players.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        with col1:
            st.text_input(
                f"Aktueller Name: {row['Spieler']}",
                value=row['Spieler'],
                key=f"player_name_{idx}",
                label_visibility="collapsed"
            )
        with col2:
            new_name = st.text_input(
                "Neuer Name",
                value="",
                placeholder="Neuen Namen eingeben",
                key=f"new_player_name_{idx}"
            )
        with col3:
            geschlecht = st.selectbox(
                "m/w",
                options=["m", "w"],
                index=0 if row["Geschlecht"] == "m" else 1,
                key=f"geschlecht_edit_{idx}",
                label_visibility="collapsed"
            )
        with col4:
            if st.button("✓", key=f"btn_rename_{idx}"):
                if new_name:
                    st.session_state.players.at[idx, "Spieler"] = new_name
                st.session_state.players.at[idx, "Geschlecht"] = geschlecht
                st.success(f"✓")
                st.rerun()

# Berechne Gesamtwerte
df = st.session_state.players.copy()
volle_cols = [f"V{i}" for i in range(1, 11)]
abr_cols = [f"A{i}" for i in range(1, 11)]
df["Volle"] = df[volle_cols].sum(axis=1)
df["Abräumen"] = df[abr_cols].sum(axis=1)
df["Gesamt"] = df["Volle"] + df["Abräumen"]

# -----------------------------
# Teamwertung
# -----------------------------
st.header("🏆 Teamwertung")

team_scores = (
    df.groupby("Team")["Gesamt"]
    .sum()
    .reset_index()
    .sort_values("Gesamt", ascending=False)
    .reset_index(drop=True)
)
team_scores.index = team_scores.index + 1
team_scores.index.name = "Platz"

st.subheader("📊 Aktuelles Ranking")
st.dataframe(team_scores, use_container_width=True)

# -----------------------------
# Top 4 & KO-Phase
# -----------------------------
st.header("🔥 KO-Phase")

if len(team_scores) >= 4:
    # Initialisiere KO-Daten im Session State
    if "ko_data" not in st.session_state:
        ko_data = []
        # Für Halbfinale: 4 Teams x 5 Spieler
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
        # Für Finale: 2 Teams x 5 Spieler
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
    st.markdown("### 🥊 Halbfinale - Spielerwürfe eingeben")

    # Team-Auswahl für Halbfinale (2 Bahnen)
    hf_teams = [top4.loc[0, 'Team'], top4.loc[1, 'Team'],
                top4.loc[2, 'Team'], top4.loc[3, 'Team']]
    hf_team_mapping = {
        top4.loc[0, 'Team']: "HF_Team_1",
        top4.loc[1, 'Team']: "HF_Team_3",
        top4.loc[2, 'Team']: "HF_Team_2",
        top4.loc[3, 'Team']: "HF_Team_4"
    }

    col_select_hf1, col_select_hf2 = st.columns(2)
    with col_select_hf1:
        st.markdown("### 🎯 Bahn 1 (Halbfinale)")
        selected_hf_team_1 = st.selectbox(
            "Team auswählen:", hf_teams, key="hf_team_bahn1")
    with col_select_hf2:
        st.markdown("### 🎯 Bahn 2 (Halbfinale)")
        default_hf_idx = min(1, len(hf_teams) - 1)
        selected_hf_team_2 = st.selectbox(
            "Team auswählen:", hf_teams, index=default_hf_idx, key="hf_team_bahn2")

    st.markdown("---")

    col_hf1, col_hf2 = st.columns(2)

    # Bahn 1 - HF Team 1
    with col_hf1:
        st.markdown(f"#### 🎳 Bahn 1: {selected_hf_team_1}")
        team_data_hf_1 = st.session_state.ko_data[
            st.session_state.ko_data["Team"] == hf_team_mapping[selected_hf_team_1]
        ].copy()

        for idx, row in team_data_hf_1.iterrows():
            with st.expander(f"🎯 {row['Spieler']}", expanded=False):
                # Volle
                st.markdown("**Volle (10 Würfe)**")
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
                            key=f"hf_b1_v_{idx}_{i}",
                            step=1,
                            label_visibility="visible"
                        )
                        st.session_state.ko_data.at[idx, f"V{i}"] = val
                        volle_sum += val

                # Abräumen
                st.markdown("**Abräumen (10 Würfe)**")
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
                            key=f"hf_b1_a_{idx}_{i}",
                            step=1,
                            label_visibility="visible"
                        )
                        st.session_state.ko_data.at[idx, f"A{i}"] = val
                        abr_sum += val
                st.success(f"**Gesamt: {volle_sum + abr_sum} Holz**")

        # Berechne Team Summe
        volle_cols_calc = [f"V{i}" for i in range(1, 11)]
        abr_cols_calc = [f"A{i}" for i in range(1, 11)]
        hf_team1_total = (
            team_data_hf_1[volle_cols_calc].sum().sum() +
            team_data_hf_1[abr_cols_calc].sum().sum()
        )
        st.metric(f"Team-Summe {selected_hf_team_1}", int(hf_team1_total))

    # Bahn 2 - HF Team 2
    with col_hf2:
        st.markdown(f"#### 🎳 Bahn 2: {selected_hf_team_2}")
        team_data_hf_2 = st.session_state.ko_data[
            st.session_state.ko_data["Team"] == hf_team_mapping[selected_hf_team_2]
        ].copy()

        for idx, row in team_data_hf_2.iterrows():
            with st.expander(f"🎯 {row['Spieler']}", expanded=False):
                # Volle
                st.markdown("**Volle (10 Würfe)**")
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
                            key=f"hf_b2_v_{idx}_{i}",
                            step=1,
                            label_visibility="visible"
                        )
                        st.session_state.ko_data.at[idx, f"V{i}"] = val
                        volle_sum += val

                # Abräumen
                st.markdown("**Abräumen (10 Würfe)**")
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
                            key=f"hf_b2_a_{idx}_{i}",
                            step=1,
                            label_visibility="visible"
                        )
                        st.session_state.ko_data.at[idx, f"A{i}"] = val
                        abr_sum += val
                st.success(f"**Gesamt: {volle_sum + abr_sum} Holz**")

        # Berechne Team Summe
        hf_team2_total = (
            team_data_hf_2[volle_cols_calc].sum().sum() +
            team_data_hf_2[abr_cols_calc].sum().sum()
        )
        st.metric(f"Team-Summe {selected_hf_team_2}", int(hf_team2_total))

    st.markdown("---")
    st.markdown("#### 🥊 Halbfinale-Ergebnisse")

    # Berechne alle 4 Team-Summen
    hf_results = {}
    for team_name, team_key in hf_team_mapping.items():
        team_df = st.session_state.ko_data[st.session_state.ko_data["Team"] == team_key]
        total = (
            team_df[volle_cols_calc].sum().sum() +
            team_df[abr_cols_calc].sum().sum()
        )
        hf_results[team_name] = int(total)

    # Initialisiere Gewinner-Variablen
    hf1_winner = None
    hf2_winner = None

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.info(
            f"**HF 1:** {top4.loc[0, 'Team']} ({hf_results[top4.loc[0, 'Team']]}) vs {top4.loc[2, 'Team']} ({hf_results[top4.loc[2, 'Team']]})")
        if hf_results[top4.loc[0, 'Team']] > hf_results[top4.loc[2, 'Team']] and hf_results[top4.loc[0, 'Team']] > 0:
            st.success(f"✅ Gewinner: **{top4.loc[0, 'Team']}**")
            hf1_winner = top4.loc[0, 'Team']
        elif hf_results[top4.loc[2, 'Team']] > hf_results[top4.loc[0, 'Team']] and hf_results[top4.loc[2, 'Team']] > 0:
            st.success(f"✅ Gewinner: **{top4.loc[2, 'Team']}**")
            hf1_winner = top4.loc[2, 'Team']
        else:
            hf1_winner = None

    with res_col2:
        st.info(
            f"**HF 2:** {top4.loc[1, 'Team']} ({hf_results[top4.loc[1, 'Team']]}) vs {top4.loc[3, 'Team']} ({hf_results[top4.loc[3, 'Team']]})")
        if hf_results[top4.loc[1, 'Team']] > hf_results[top4.loc[3, 'Team']] and hf_results[top4.loc[1, 'Team']] > 0:
            st.success(f"✅ Gewinner: **{top4.loc[1, 'Team']}**")
            hf2_winner = top4.loc[1, 'Team']
        elif hf_results[top4.loc[3, 'Team']] > hf_results[top4.loc[1, 'Team']] and hf_results[top4.loc[3, 'Team']] > 0:
            st.success(f"✅ Gewinner: **{top4.loc[3, 'Team']}**")
            hf2_winner = top4.loc[3, 'Team']
        else:
            hf2_winner = None

    st.markdown("---")
    st.markdown("### 🏆 Finale")

    # Finale nur anzeigen, wenn beide Halbfinals entschieden sind
    if hf1_winner and hf2_winner:
        # Finale Team-Auswahl (2 Bahnen)
        finale_teams = [hf1_winner, hf2_winner]
        finale_team_mapping = {
            hf1_winner: "Finale_Team_1",
            hf2_winner: "Finale_Team_2"
        }

        col_select_f1, col_select_f2 = st.columns(2)
        with col_select_f1:
            st.markdown("### 🎯 Bahn 1 (Finale)")
            selected_finale_team_1 = st.selectbox(
                "Team auswählen:", finale_teams, key="finale_team_bahn1")
        with col_select_f2:
            st.markdown("### 🎯 Bahn 2 (Finale)")
            default_f_idx = 1 if len(finale_teams) > 1 else 0
            selected_finale_team_2 = st.selectbox(
                "Team auswählen:", finale_teams, index=default_f_idx, key="finale_team_bahn2")

        st.markdown("---")

        finale_col1, finale_col2 = st.columns(2)

        # Finale Bahn 1
        with finale_col1:
            st.markdown(f"#### 🎳 Bahn 1: {selected_finale_team_1}")
            team_data_finale_1 = st.session_state.ko_data[
                st.session_state.ko_data["Team"] == finale_team_mapping[selected_finale_team_1]
            ].copy()

            for idx, row in team_data_finale_1.iterrows():
                with st.expander(f"🎯 {row['Spieler']}", expanded=False):
                    # Volle
                    st.markdown("**Volle (10 Würfe)**")
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
                                key=f"finale_b1_v_{idx}_{i}",
                                step=1,
                                label_visibility="visible"
                            )
                            st.session_state.ko_data.at[idx, f"V{i}"] = val
                            volle_sum += val

                    # Abräumen
                    st.markdown("**Abräumen (10 Würfe)**")
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
                                key=f"finale_b1_a_{idx}_{i}",
                                step=1,
                                label_visibility="visible"
                            )
                            st.session_state.ko_data.at[idx, f"A{i}"] = val
                            abr_sum += val
                    st.success(f"**Gesamt: {volle_sum + abr_sum} Holz**")

            # Berechne Finale Team 1 Summe
            volle_cols_calc = [f"V{i}" for i in range(1, 11)]
            abr_cols_calc = [f"A{i}" for i in range(1, 11)]
            finale_team1_total = (
                team_data_finale_1[volle_cols_calc].sum().sum() +
                team_data_finale_1[abr_cols_calc].sum().sum()
            )
            st.metric(
                f"Team-Summe {selected_finale_team_1}", int(finale_team1_total))

        # Finale Bahn 2
        with finale_col2:
            st.markdown(f"#### 🎳 Bahn 2: {selected_finale_team_2}")
            team_data_finale_2 = st.session_state.ko_data[
                st.session_state.ko_data["Team"] == finale_team_mapping[selected_finale_team_2]
            ].copy()

            for idx, row in team_data_finale_2.iterrows():
                with st.expander(f"🎯 {row['Spieler']}", expanded=False):
                    # Volle
                    st.markdown("**Volle (10 Würfe)**")
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
                                key=f"finale_b2_v_{idx}_{i}",
                                step=1,
                                label_visibility="visible"
                            )
                            st.session_state.ko_data.at[idx, f"V{i}"] = val
                            volle_sum += val

                    # Abräumen
                    st.markdown("**Abräumen (10 Würfe)**")
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
                                key=f"finale_b2_a_{idx}_{i}",
                                step=1,
                                label_visibility="visible"
                            )
                            st.session_state.ko_data.at[idx, f"A{i}"] = val
                            abr_sum += val
                    st.success(f"**Gesamt: {volle_sum + abr_sum} Holz**")

            # Berechne Finale Team 2 Summe
            finale_team2_total = (
                team_data_finale_2[volle_cols_calc].sum().sum() +
                team_data_finale_2[abr_cols_calc].sum().sum()
            )
            st.metric(
                f"Team-Summe {selected_finale_team_2}", int(finale_team2_total))

        st.markdown("---")
        st.markdown("#### 🏆 Finale-Ergebnis")

        # Berechne beide Finale-Team-Summen
        finale_results = {}
        for team_name, team_key in finale_team_mapping.items():
            team_df = st.session_state.ko_data[st.session_state.ko_data["Team"] == team_key]
            total = (
                team_df[volle_cols_calc].sum().sum() +
                team_df[abr_cols_calc].sum().sum()
            )
            finale_results[team_name] = int(total)

        st.info(
            f"**{hf1_winner}** ({finale_results[hf1_winner]}) vs **{hf2_winner}** ({finale_results[hf2_winner]})")

        # Initialisiere Balloons-State
        if "balloons_shown" not in st.session_state:
            st.session_state.balloons_shown = False

        # Turniersieger ermitteln
        winner_decided = False
        tournament_winner = None

        if hf1_winner and hf2_winner:
            if finale_results[hf1_winner] > finale_results[hf2_winner] and finale_results[hf1_winner] > 0:
                winner_decided = True
                tournament_winner = hf1_winner
            elif finale_results[hf2_winner] > finale_results[hf1_winner] and finale_results[hf2_winner] > 0:
                winner_decided = True
                tournament_winner = hf2_winner

            # Zeige Sieger und Balloons nur einmal
            if winner_decided:
                if not st.session_state.balloons_shown:
                    st.balloons()
                    st.session_state.balloons_shown = True
                st.success(f"# 🏆 TURNIERSIEGER: **{tournament_winner}** 🏆")
            else:
                st.session_state.balloons_shown = False
                st.info("⚡ Finale-Ergebnis eingeben für den Turniersieger!")

        else:
            st.info("⏳ Warte auf Halbfinal-Ergebnisse...")

# -----------------------------
# Spielerwertung
# -----------------------------
st.header("👤 Spielerwertung")

# Top 10 Spieler gesamt
st.subheader("🥇 Top 10 Spieler (Gesamt)")
top_players = df.sort_values("Gesamt", ascending=False).head(10)[
    ["Spieler", "Team", "Geschlecht", "Volle", "Abräumen", "Gesamt"]
].reset_index(drop=True)
top_players.index = top_players.index + 1
top_players.index.name = "Rang"
st.dataframe(top_players, use_container_width=True)

# Top 5 Frauen
st.subheader("👩 Top 5 Frauen")
top_female = df[df["Geschlecht"] == "w"].sort_values(
    "Gesamt", ascending=False
).head(5)[["Spieler", "Team", "Volle", "Abräumen", "Gesamt"]].reset_index(drop=True)

if not top_female.empty:
    top_female.index = top_female.index + 1
    top_female.index.name = "Rang"
    st.dataframe(top_female, use_container_width=True)
else:
    st.info("Noch keine weiblichen Spieler erfasst")

# Beste Ergebnisse
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

st.caption("💡 Live-Auswertung – Änderungen werden sofort übernommen")
