# BigRed WebSocket Client

## Overview

The BigRed WebSocket Client is a Python 3 script designed to locate NetScout nGeniusPULSE devices (e.g., nPoints) running a WebSocket server on port 8000 within a specified IPv4 network. It queries devices for attributes such as MAC address, build version, CPU temperature, and system information, and logs results to a file. The script is optimized for embedded systems, using the `websockets` library for WebSocket communication (see `requirements.txt`).

This utility is intended for network administrators monitoring network performance and infrastructure health with NetScout’s nGeniusPULSE solution.

## Features

- Scans an IPv4 network for nGeniusPULSE devices with WebSocket port 8000 open.
- Queries devices for attributes like MAC address, build version, and system status.
- Supports filtering by MAC address suffix.
- Logs detailed debugging information to `bigred_websocket.log`.
- Outputs results to the console with customizable detail levels (0-9).
- Supports English and Spanish output.
- Uses asynchronous I/O (`asyncio`) for efficient scanning.
- Provides verbose console output option for real-time feedback.

## Requirements

- Python 3.6 or later.
- Dependencies listed in `requirements.txt` (install with `pip install -r requirements.txt`).
- Access to the target network.
- Write permissions for the log file.
- Network configured for bridged connections (for VMs).

## Installation

1. Install Python 3.6 or later on your system.
2. Clone or download the project repository.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure the script has executable permissions:
   ```bash
   chmod +x BigRedWebSocketClient.py
   ```

## Usage

Run the script with optional command-line arguments:

```bash
./BigRedWebSocketClient.py -i 192.168.1.0/24
```

### Command-Line Options

- `-i, --network NETWORK`: IPv4 network in CIDR notation (default: 129.196.196.0/23).
- `-m, --mac-filter MAC`: MAC address suffix filter (e.g., 330030).
- `-t, --timeout SECONDS`: Timeout in seconds (default: 0.10).
- `-d, --display-level LEVEL`: Info level (0=minimal, 9=full; default: 0).
- `-l, --language {EN,ES}`: Language (EN=English, ES=Spanish; default: EN).
- `-v, --version`: Display the script version (3.0.0).
- `--verbose`: Enable verbose console output.

### Example Commands

Scan the 192.168.1.0/24 network with default settings:

```bash
./BigRedWebSocketClient.py -i 192.168.1.0/24
```

Scan with a MAC filter and verbose output:

```bash
./BigRedWebSocketClient.py -i 192.168.1.0/24 -m 330030 --verbose
```

Scan with Spanish output and full detail:

```bash
./BigRedWebSocketClient.py -i 192.168.1.0/24 -l ES -d 9
```

## Output

- **Log File**: `bigred_websocket.log` contains detailed debug and info messages, including scan progress, errors, and a summary.
- **Console Output**: Displays discovered nGeniusPULSE devices with attributes based on the display level.

Example console output (display level 0):

```
Scan IP Network: 192.168.1.0/24
Scan Begin Addr: 192.168.1.1
Scan End Addr:   192.168.1.254

IP Address= 192.168.1.100
MAC Address= 00:c0:17:33:00:30
Build Version= 2.1.3

DONE
Total nGeniusPULSE devices found= 1
```

## Project Structure

```
bigred-websocket-client/
├── archive/
│   └── v2.10/
│       └── BigRedWebSocketClient.py  # Original script (version 2.10)
├── BigRedWebSocketClient.py          # Current script (version 3.0.0)
├── requirements.txt                  # Dependency list
├── README.md                         # Project documentation
├── changelog.txt                     # Version history
├── bump_version.py                   # Version increment script
└── .gitignore                        # Git ignore rules
```

- The `archive/v2.10/` folder contains the original script for reference.
- The root folder holds the active development files.

## Development

### Installation for Development

```bash
git clone <repository-url>
cd bigred-websocket-client
pip install -r requirements.txt
```

### Versioning

To increment the version number and update the changelog, use the `bump_version.py` script:

```bash
python3 bump_version.py "Added new feature X"
```

This increments the patch version (e.g., 3.0.0 to 3.0.1), updates `BigRedWebSocketClient.py`, and appends a changelog entry.

### Git Workflow

- **Branches**:
  - `main`: Stable, production-ready code.
  - `develop`: Integration branch for new features and fixes.
  - Feature/bugfix branches: Named `feature/<name>` or `bugfix/<name>`.
- **Commit Messages**:
  - Format: `<type>(<scope>): <description>`
  - Types: `feat`, `fix`, `docs`, `refactor`, `chore`.
  - Example: `feat(scanning): Add IPv6 support`

## Notes

- **WebSocket Dependency**: The script uses the `websockets` library (see `requirements.txt`). Ensure it’s installed or bundled for embedded systems.
- **Original Script**: The original version (2.10) is archived in `archive/v2.10/` for reference. It relies on `websocket-client` and `netaddr`, which are not used in the current version.
- **Async I/O**: The script uses `asyncio` for efficient scanning, suitable for large networks.
- **Log File**: The log file is overwritten on each run to manage storage.
- **Interrupt Handling**: Use `Ctrl+C` to stop scanning gracefully.

## Known Limitations

- Only IPv4 networks are supported.
- No support for IPv6 or non-WebSocket protocols.
- The `uptime` query is disabled due to incorrect system clock reporting.

## Contributing

This script is maintained by Kris Armstrong. For bug reports or feature requests, contact the NetScout support team.

## License

This software is proprietary and intended for use with NetScout nGeniusPULSE devices. Unauthorized distribution or modification is prohibited.

## Version

3.0.0 (April 18, 2025)