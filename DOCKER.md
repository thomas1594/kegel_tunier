# Kegelturnier App - Docker Setup

## Schnellstart

### Mit Docker Compose (empfohlen)

```bash
# App starten
docker-compose up -d

# Logs anschauen
docker-compose logs -f

# App stoppen
docker-compose down
```

Die App ist dann verfügbar unter: http://localhost:8501

### Nur mit Docker

```bash
# Image bauen
docker build -t kegelturnier .

# Container starten mit Volume
docker run -d \
  --name kegelturnier \
  -p 8501:8501 \
  -v kegelturnier-data:/app/data \
  kegelturnier
```

## Datenbank

Die SQLite-Datenbank wird im Docker Volume `kegelturnier-data` gespeichert und bleibt auch nach Container-Neustarts erhalten.

### Datenbank-Backup erstellen

```bash
# Datenbank aus dem Volume kopieren
docker run --rm \
  -v kegelturnier-data:/data \
  -v $(pwd):/backup \
  alpine cp /data/kegelturnier.db /backup/kegelturnier_backup.db
```

### Datenbank wiederherstellen

```bash
# Backup in das Volume kopieren
docker run --rm \
  -v kegelturnier-data:/data \
  -v $(pwd):/backup \
  alpine cp /backup/kegelturnier_backup.db /data/kegelturnier.db
```

## Lokale Entwicklung

Für lokale Entwicklung ohne Docker:

```bash
# Dependencies installieren
pip install -r requirements.txt

# App starten (Datenbank wird im lokalen 'data' Ordner gespeichert)
streamlit run kegel.py
```

## Umgebungsvariablen

- `DB_DIR`: Verzeichnis für die Datenbank (Standard: `data`)

Im Docker-Container wird die Datenbank standardmäßig in `/app/data` gespeichert, welches mit dem Volume gemountet ist.
