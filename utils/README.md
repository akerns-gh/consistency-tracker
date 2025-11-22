# Utils Directory

This directory contains utility scripts for the True Lacrosse Consistency Tracker prototype.

## start-server.sh

A bash script to easily start a local HTTP server for testing the prototype.

### Usage

```bash
./utils/start-server.sh
```

Or from the project root:

```bash
bash utils/start-server.sh
```

### Features

- Automatically detects available server tools (Python 3, Python 2, Node.js, or PHP)
- Uses port 8000 by default, falls back to 8001 if 8000 is in use
- Changes to the prototype directory automatically
- Provides clear output with server URL

### Requirements

The script will try to use one of the following (in order):
1. Python 3 (`python3 -m http.server`)
2. Python 2 (`python -m SimpleHTTPServer`)
3. Node.js (`npx http-server`)
4. PHP (`php -S`)

### Accessing the Prototype

Once the server is running, open your browser and navigate to:
- http://localhost:8000 (or the port shown in the output)

### Stopping the Server

Press `Ctrl+C` in the terminal to stop the server.

