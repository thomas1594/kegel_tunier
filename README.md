# 🎳 Kegelturnier - Live Auswertung

Eine Streamlit-basierte Web-Anwendung zur Verwaltung und Live-Auswertung von Kegelturnieren mit Vorrunde, Halbfinale und Finale.

## 📋 Features

### Turnierverwaltung
- **Vorrunde**: 10 Teams à 5 Spieler mit paralleler 2-Bahnen-Eingabe
- **Halbfinale**: Top 4 Teams (1. vs 3., 2. vs 4.)
- **Finale**: Gewinner der beiden Halbfinals
- **Live-Rankings**: Automatische Berechnung und Sortierung

### Eingabemodus
- Strukturierte Eingabe: Erst alle "Volle", dann alle "Abräumen" pro Team
- Je 10 Würfe pro Kategorie (5 Würfe pro Bahn angezeigt)
- Eingeklappt standardmäßig für bessere Übersicht

### Auswertungen
- 🏅 **Turnier-Platzierung**: Top 4 Teams mit Holzzahlen
- 🏆 **Teamwertung**: Komplette Rangliste aller Teams
- 🎯 **Beste Einzelergebnisse**:
  - Bester Spieler (gesamt)
  - Beste Frau
  - Beste Volle
- 🥇 **Top 10 Spieler**: Individuelle Bestenliste

### Verwaltung
- Team- und Spielernamen bearbeiten
- Geschlechter-Zuordnung (m/w)
- Excel-Export (lokal & Download)
- Live-Speicherung aller Änderungen

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher

### Setup
```bash
# Repository klonen
git clone https://github.com/thomas1594/kegel_tunier.git
cd kegel_tunier

# Virtuelle Umgebung erstellen (optional, empfohlen)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oder
.venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## 💻 Nutzung

### Anwendung starten
```bash
streamlit run kegel.py
```

Die Anwendung öffnet sich automatisch im Browser unter `http://localhost:8501`

### Workflow

1. **Vorrunde eingeben**
   - Wähle 2 Teams für Bahn 1 und Bahn 2
   - Expandiere "Auf die Vollen" und gib alle Würfe ein
   - Expandiere "Abräumen" und gib alle Würfe ein
   - Wiederhole für alle Teams

2. **Halbfinale durchführen**
   - Top 4 Teams werden automatisch qualifiziert
   - HF1: 1. Platz vs 3. Platz
   - HF2: 2. Platz vs 4. Platz
   - Eingabe wie in der Vorrunde

3. **Finale austragen**
   - Gewinner der beiden Halbfinals treten an
   - Eingabe wie zuvor

4. **Auswertung ansehen**
   - Platzierungen 1-4 prominent angezeigt
   - Vollständige Rankings und Statistiken
   - Top 10 Spieler

5. **Daten exportieren**
   - "💾 Lokal Speichern" für lokale Datei
   - "📥 Excel Download" für Browser-Download

## 📁 Projektstruktur

```
kegel_tunier/
├── kegel.py              # Hauptanwendung (Streamlit UI)
├── functions.py          # Hilfsfunktionen
├── requirements.txt      # Python-Abhängigkeiten
└── README.md            # Diese Datei
```

## 🔧 Technische Details

### Abhängigkeiten
- **streamlit**: Web-Framework für die UI
- **pandas**: Datenverarbeitung und -verwaltung
- **openpyxl**: Excel-Export-Funktionalität

### Datenstruktur
- **Session State**: Persistente Datenspeicherung während der Sitzung
- **DataFrame**: Spielerdaten (50 Spieler, 10 Teams)
- **KO-Daten**: Separate Struktur für Halbfinale und Finale

### Features im Detail
- Auto-Save: Änderungen werden sofort übernommen
- Unique Keys: Vermeidung von Duplikaten durch teamspezifische Keys
- Responsive Design: Spalten-Layout passt sich an

## 📊 Datenformat

### Vorrunde
- Team: Team 1-10
- Spieler: Spieler 1-5 pro Team
- V1-V10: 10 Würfe "Auf die Vollen"
- A1-A10: 10 Würfe "Abräumen"
- Geschlecht: m/w

### Berechnung
- **Volle**: Summe V1-V10
- **Abräumen**: Summe A1-A10
- **Gesamt**: Volle + Abräumen

## 🤝 Mitwirken

Contributions sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

## 📝 Lizenz

Dieses Projekt ist Open Source.

## 👨‍💻 Autor

Thomas (thomas1594)

## 🎯 Zukünftige Features (optional)

- [ ] Datenbank-Backend für permanente Speicherung

---

**Viel Erfolg beim Turnier! 🎳🏆**
