# City of Heroes - Combat Parser

## Project Overview

This is a Python-based combat log parser for City of Heroes, a popular MMORPG. The application reads and parses combat chat logs to provide real-time and historical combat statistics including damage output, DPS calculations, hit accuracy, and per-ability breakdowns.

**Current Status**: ALPHA - Expect bugs and possible data inaccuracies

**Author**: @10kVolts
**Repository**: https://github.com/dorematt/coh-combat-parser/

## Tech Stack

- **Language**: Python 3.12 (required - not compatible with 3.13+)
- **GUI Framework**: PyQt5 5.15.10
- **Build Tool**: PyInstaller 6.3.0 (for creating standalone executables)
- **Platform**: Cross-platform (Windows, Linux, Mac)

## Project Structure

```
coh-combat-parser/
├── src/
│   ├── CoH_Parser.py          # Main entry point
│   ├── combat/                # Combat parsing logic
│   │   ├── Ability.py         # Ability data model
│   │   ├── Character.py       # Character data model
│   │   ├── CombatParser.py    # Core parsing engine
│   │   ├── CombatSession.py   # Session management
│   │   └── DamageComponent.py # Damage calculation
│   ├── data/                  # Data models and patterns
│   │   ├── Globals.py         # Global constants and settings
│   │   ├── LogPatterns.py     # Regex patterns for log parsing
│   │   └── pseudopets.py      # Pseudopet definitions
│   └── ui/                    # User interface
│       ├── MainUI.py          # Main application window
│       ├── Settings.py        # Settings dialog
│       ├── icon/              # Application icons
│       └── style/             # Qt stylesheets and themes
│           ├── Theme.py
│           ├── stylesheet.qss
│           └── Combinear.qss
├── deploysettings/            # Deployment configuration
├── requirements.txt           # Python dependencies
├── run.sh                     # Linux/Mac launcher
├── run.bat                    # Windows launcher
└── README.md                  # User documentation
```

## Development Setup

### Quick Start (Recommended)

1. Ensure Python 3.12 is installed (check with `python --version` or `python3 --version`)
2. Clone the repository
3. Run the launcher script:
   - Linux/Mac: `./run.sh`
   - Windows: `run.bat`

The launcher automatically creates a virtual environment, installs dependencies, and starts the application.

### Manual Setup

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/CoH_Parser.py
```

## Key Components

### Combat Parsing System

- **CombatParser.py**: Core parsing engine that reads log files and extracts combat events
- **CombatSession.py**: Manages combat sessions (starts on ability activation, ends after 15s of inactivity)
- **Ability.py**: Tracks individual ability statistics (damage, activation count, accuracy)
- **Character.py**: Represents players and their combat data
- **DamageComponent.py**: Handles damage calculation and categorization

### Data Layer

- **Globals.py**: Application-wide constants including version, build info, and default settings
- **LogPatterns.py**: Regular expression patterns for parsing City of Heroes combat log format
- **pseudopets.py**: Definitions for pseudo-pets (temporary entities that deal damage on behalf of the player)

### UI Layer

- **MainUI.py**: Main application window with combat statistics display
- **Settings.py**: User preferences and configuration
- **Theme.py**: Qt stylesheet manager for consistent UI styling

## Important Constants (Globals.py)

- `VERSION`: Current version number
- `BUILD_TYPE`: "ALPHA", "BETA", or "RELEASE"
- `DEFAULT_COMBAT_SESSION_TIMEOUT`: 15 seconds (time after last damage before session ends)
- `DEFAULT_ASSOCIATE_PROCS_TO_POWERS`: Associates proc damage with triggering abilities
- `NO_HIT_ABILITIES`: Abilities that don't track hit/miss (like Interface procs)

## Features

### Current Capabilities

- Real-time and historical combat log parsing
- Outgoing damage tracking (player + pets)
- DPS calculation (overall and per-session)
- Per-ability statistics (damage, activations, average damage, accuracy)
- Damage type and flair tracking (Crits, procs, etc.)
- Automatic combat session splitting
- Custom session naming (type `##SESSION_NAME Session` in local chat)

### Session Management

- Sessions auto-start when an ability is activated
- Sessions end 15 seconds after the last damage event
- Duration measured from first to last damaging ability
- Users can rename sessions via in-game chat commands

## Development Guidelines

### Code Style

- Follow PEP 8 conventions for Python code
- Use descriptive variable names
- Keep functions focused and modular
- Add comments for complex parsing logic or game-specific mechanics

### Working with Combat Logs

- Log format is specific to City of Heroes chat system
- All combat channels must be enabled in-game for complete data
- Log parsing relies on regex patterns defined in LogPatterns.py
- Be careful with pseudo-pet attribution to avoid double-counting damage

### Testing

- Test with actual City of Heroes log files (found in game installation under `/accounts/ACCOUNT_NAME/logs/`)
- Verify accuracy against in-game combat numbers
- Test both real-time parsing and historical log analysis
- Ensure session splitting works correctly with varying combat patterns

## Building Executables

The project uses PyInstaller to create standalone executables:

```bash
pyinstaller --name="CoH_Parser" \
    --onefile \
    --windowed \
    --icon=src/ui/icon/icon_256.ico \
    src/CoH_Parser.py
```

Configuration details are in `deploysettings/`.

## Common Tasks

### Updating Version Info

Edit `src/data/Globals.py`:
- Update `VERSION`
- Update `BUILD_DATE`
- Update `BUILD_TYPE` as needed

### Adding New Log Patterns

Edit `src/data/LogPatterns.py` and add new regex patterns for combat events.

### Modifying UI Styling

Edit stylesheets in `src/ui/style/`:
- `stylesheet.qss`: Main application styles
- `Combinear.qss`: Alternate theme
- `Theme.py`: Theme management

### Adding New Combat Statistics

1. Update relevant data model (Ability.py, Character.py, etc.)
2. Modify CombatParser.py to extract the data
3. Update MainUI.py to display the new statistics

## Known Issues & Limitations

- ALPHA software - expect bugs and inaccuracies
- Requires Python 3.12 (not compatible with 3.13+)
- Relies on City of Heroes chat logging being enabled
- Only tracks outgoing damage (not incoming)

## Git Workflow

- Main development branch: `main` (or master)
- Feature branches: Use descriptive names
- Always test changes with actual game log files before committing

## Contact & Support

- GitHub Issues: https://github.com/dorematt/coh-combat-parser/issues
- In-game: @10kVolts
- HC Forums: @10kvolts (Discord)
- Forum thread: https://forums.homecomingservers.com/topic/47397-tenkays-standalone-log-combat-parser/

## Additional Notes

- The application reads log files but does not modify them
- Performance is optimized for real-time parsing during gameplay
- Combat data is session-based to allow per-encounter analysis
- Pseudo-pet damage is correctly attributed to the player who summoned them
