# 🎳 Bowling Tournament - Live Scoring

A Streamlit-based web application for managing and live-scoring bowling tournaments with preliminary round, semifinals, and finals.

## 📋 Features

### Tournament Management
- **Preliminary Round**: 10 teams with 5 players each, parallel 2-lane input
- **Semifinals**: Top 4 teams (1st vs 3rd, 2nd vs 4th)
- **Finals**: Winners of both semifinals
- **Live Rankings**: Automatic calculation and sorting
- **Auto-Save**: SQLite database ensures no data loss

### Input Mode
- Structured input: All "Volle" (full pins) first, then all "Abräumen" (spare attempts) per team
- 10 throws per category (5 throws per lane displayed)
- Collapsed by default for better overview

### Statistics & Rankings
- 🏅 **Tournament Placement**: Top 4 teams with scores
- 🏆 **Team Rankings**: Complete ranking of all teams
- 🎯 **Best Individual Results**:
  - Best Player (overall)
  - Best Female Player
  - Best "Volle" (full pins)
- 🥇 **Top 10 Players**: Individual leaderboard

### Data Management
- Edit team and player names
- Gender assignment (m/f)
- Excel export (local file & browser download)
- **Auto-save**: Every throw is automatically saved to SQLite database
- **Crash-proof**: Data persists across sessions and browser refreshes
- Reset tournament for new competitions

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher

### Setup
```bash
# Clone repository
git clone https://github.com/thomas1594/kegel_tunier.git
cd kegel_tunier

# Create virtual environment (optional, recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 🐳 Docker Setup

The app can also be run with Docker. See [DOCKER.md](DOCKER.md) for full details.

#### With Docker Compose (recommended)

```bash
# Start the app
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the app
docker-compose down
```

The app is then available at `http://localhost:8501`.

#### With plain Docker

```bash
# Build the image
docker build -t kegelturnier .

# Run the container with a persistent volume
docker run -d \
  --name kegelturnier \
  -p 8501:8501 \
  -v kegelturnier-data:/app/data \
  kegelturnier
```

#### Database & environment variables

The SQLite database is stored in the `kegelturnier-data` Docker volume so it persists across container restarts. The database directory can be configured via the `DB_DIR` environment variable (default: `data`, in the container: `/app/data`).

#### Docker in WSL 2

`install-docker-wsl.sh` installs Docker Engine and the Compose plugin inside WSL 2.

## 💻 Usage

### Start Application
```bash
streamlit run kegel.py
```

The application opens automatically in your browser at `http://localhost:8501`

### Workflow

1. **Enter Preliminary Round Data**
   - Select 2 teams for Lane 1 and Lane 2
   - Expand "Auf die Vollen" and enter all throws
   - Expand "Abräumen" and enter all throws
   - Data is automatically saved after each throw
   - Repeat for all teams

2. **Conduct Semifinals**
   - Top 4 teams are automatically qualified
   - SF1: 1st place vs 3rd place
   - SF2: 2nd place vs 4th place
   - Input same as preliminary round

3. **Play Finals**
   - Winners of both semifinals compete
   - Input same as before

4. **View Statistics**
   - Placements 1-4 prominently displayed
   - Complete rankings and statistics
   - Top 10 players

5. **Export Data**
   - "💾 Lokal Speichern" for local Excel file
   - "📥 Excel Download" for browser download
   - "🔄 Neues Turnier" to reset and start fresh

## 📁 Project Structure

```
kegel_tunier/
├── kegel.py                # Main application (Streamlit UI)
├── functions.py            # Helper functions
├── requirements.txt        # Python dependencies
├── data/
│   └── kegelturnier.db     # SQLite database (auto-created)
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose service configuration
├── .dockerignore           # Files excluded from the Docker build
├── install-docker-wsl.sh   # Docker installation script for WSL 2
├── DOCKER.md               # Detailed Docker documentation
└── README.md               # This file
```

## 🔧 Technical Details

### Dependencies
- **streamlit**: Web framework for UI
- **pandas**: Data processing and management
- **openpyxl**: Excel export functionality
- **sqlite3**: Database (included in Python standard library)

### Data Structure
- **SQLite Database**: Persistent storage with auto-save
  - `players` table: Preliminary round data
  - `ko_data` table: Semifinals and finals data
  - `tournaments` table: Tournament metadata
- **Session State**: In-memory data during active session
- **DataFrame**: Player data (50 players, 10 teams)
- **KO Data**: Separate structure for semifinals and finals

### Features in Detail
- **Auto-Save**: Every throw is immediately saved to database
- **Crash Recovery**: Data persists across sessions and crashes
- **Unique Keys**: Avoids duplicates through team-specific keys
- **Responsive Design**: Column layout adapts to screen size

## 📊 Data Format

### Preliminary Round
- Team: Team 1-10
- Player: Player 1-5 per team
- V1-V10: 10 throws "full pins"
- A1-A10: 10 throws "spare attempts"
- Gender: m/f

### Calculation
- **Full Pins (Volle)**: Sum of V1-V10
- **Spare Attempts (Abräumen)**: Sum of A1-A10
- **Total (Gesamt)**: Full Pins + Spare Attempts

## 🤝 Contributing

Contributions are welcome! Please create a Pull Request or open an Issue.

## 📝 License

This project is Open Source.

## 👨‍💻 Author

Thomas (thomas1594)

## 🎯 Future Features (optional)

- [ ] PDF export of results
- [ ] Print view for tournament tables
- [ ] Graphical statistics and charts
- [ ] Import previous tournaments
- [ ] Multi-user support
- [ ] Cloud database backend

---

**Good luck at the tournament! 🎳🏆**

**Viel Erfolg beim Turnier! 🎳🏆**
