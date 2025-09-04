# API-BOTPI

Utility for discovering public APIs. It provides both a command-line interface and a simple desktop GUI.

## Desktop App

Launch the Tkinter-based desktop application:

```bash
python -m api_bot.gui.app
```

## Command Line Interface

Run the text-based menu:

```bash
python -m api_bot.cli.commands
```

The CLI supports searching APIs, managing keys, updating the database, and exporting results.

## Web Interface

Run a minimal Flask web application that exposes search and statistics endpoints:

```bash
python -m api_bot.web.app
```

The server hosts a small HTML page at `http://localhost:5000` for interactive searches.
Additional JSON endpoints are available:

| Endpoint        | Description                         |
|-----------------|-------------------------------------|
| `/health`       | health check with timestamp/version |
| `/api/search`   | POST search API                     |
| `/api/stats`    | database statistics                 |

Cross-origin requests are permitted when `flask_cors` is installed, enabling access from
browser extensions or other local tools.
