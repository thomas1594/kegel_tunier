"""
Hilfsfunktionen für die Kegelturnier-App
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io


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
    df_export["Gesamt"] = df_export["Volle_Summe"] + df_export["Abräumen_Summe"]

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
    df_export["Gesamt"] = df_export["Volle_Summe"] + df_export["Abräumen_Summe"]

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


def update_player_name(idx, team):
    """Callback-Funktion zum automatischen Speichern des Spielernamens."""
    new_name = st.session_state[f"player_name_{team}_{idx}"]
    st.session_state.players.at[idx, "Spieler"] = new_name
    st.session_state.last_edited_team = team


def update_geschlecht(idx, team):
    """Callback-Funktion zum automatischen Speichern des Geschlechts."""
    new_geschlecht = st.session_state[f"geschlecht_edit_{team}_{idx}"]
    st.session_state.players.at[idx, "Geschlecht"] = new_geschlecht
    st.session_state.last_edited_team = team


def calculate_totals(df):
    """Berechnet Gesamtwerte für einen DataFrame."""
    volle_cols = [f"V{i}" for i in range(1, 11)]
    abr_cols = [f"A{i}" for i in range(1, 11)]
    df["Volle"] = df[volle_cols].sum(axis=1)
    df["Abräumen"] = df[abr_cols].sum(axis=1)
    df["Gesamt"] = df["Volle"] + df["Abräumen"]
    return df


def get_team_scores(df):
    """Berechnet Team-Rankings."""
    team_scores = df.groupby("Team").agg({
        "Volle": "sum",
        "Abräumen": "sum",
        "Gesamt": "sum"
    }).reset_index()
    team_scores = team_scores.sort_values("Gesamt", ascending=False).reset_index(drop=True)
    team_scores.insert(0, "Rang", range(1, len(team_scores) + 1))
    return team_scores
