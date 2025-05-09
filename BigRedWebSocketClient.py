#!/usr/bin/env python

"""
BigRed WebSocket Client
=======================

This script scans a specified IPv4 network to discover NetScout nGeniusPULSE devices
(e.g., nPoints) running a WebSocket server on port 8000. It queries devices for
attributes such as MAC address, build version, and system information, and logs
results to a file. The script is designed for embedded systems, using Python 3
with the 'websockets' library as an external dependency (see requirements.txt).

Author: Kris Armstrong
Version: 3.0.0
Date: April 18, 2025
"""

__title__ = "BigRed WebSocket Client"
__author__ = "Kris Armstrong"
__version__ = "3.0.0"

# Standard Library Imports
import argparse
import asyncio
import hashlib
import ipaddress
import logging
from datetime import datetime
import sys

# External Dependency (see requirements.txt)
import websockets

# Global Configuration
class Config:
    """Global configuration constants for the BigRed WebSocket Client."""
    default_network = "129.196.196.0/23"  # Default network (Fluke Colorado)
    timeout_secs = 0.10  # Default timeout in seconds
    log_file = "bigred_websocket.log"  # Log file for debugging and info
    websocket_port = 8000  # WebSocket port for nGeniusPULSE devices
    max_display_level = 9  # Maximum display info level


def setup_logging(verbose=False):
    """Configure logging to write to a file with a standardized format.

    Args:
        verbose (bool): If True, also log to console.
    """
    logging.basicConfig(
        filename=Config.log_file,
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logging.getLogger().addHandler(console_handler)


def parse_arguments():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.

    Raises:
        SystemExit: If arguments are invalid.
    """
    parser = argparse.ArgumentParser(
        description="Discover NetScout nGeniusPULSE devices via WebSocket on a network."
    )
    parser.add_argument(
        "-i",
        "--network",
        default=Config.default_network,
        help=f"IPv4 network in CIDR notation (default: {Config.default_network})",
    )
    parser.add_argument(
        "-m",
        "--mac-filter",
        default="",
        help="MAC address suffix filter (e.g., 330030 or 00c017330030)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=Config.timeout_secs,
        help=f"Timeout in seconds (default: {Config.timeout_secs})",
    )
    parser.add_argument(
        "-d",
        "--display-level",
        type=int,
        default=0,
        choices=range(Config.max_display_level + 1),
        help="Display info level: 0=minimal, 9=full (default: 0)",
    )
    parser.add_argument(
        "-l",
        "--language",
        choices=["EN", "ES"],
        default="EN",
        help="Language: EN=English, ES=Spanish (default: EN)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose console output",
    )

    args = parser.parse_args()

    # Validate network
    try:
        ipaddress.ip_network(args.network, strict=False)
    except ValueError as err:
        parser.error(f"Invalid network address: {args.network} ({err})")

    # Validate timeout
    if args.timeout <= 0:
        parser.error("Timeout must be positive")

    return args


async def query_device(ip_addr, queries, timeout, display_level, language, mac_filter):
    """Query a NetScout nGeniusPULSE device via WebSocket for specified attributes.

    Args:
        ip_addr (str): IP address of the device.
        queries (dict): Dictionary of query keys and display names.
        timeout (float): Timeout for WebSocket operations.
        display_level (int): Level of information to display (0-9).
        language (str): Language code ("EN" or "ES").
        mac_filter (str): MAC address suffix filter (empty if none).

    Returns:
        bool: True if a valid device was found, False otherwise.
    """
    server_url = f"ws://{ip_addr}:{Config.websocket_port}"
    nonce = None
    mac_filter_found = False

    try:
        async with websockets.connect(server_url, timeout=timeout) as ws:
            # Receive initial nonce
            result = await ws.recv()
            logging.debug("Received from %s: %s", ip_addr, result)
            nonce = result.partition('nonce": "')[2].partition('", "uname')[0]
            if not nonce:
                logging.debug("No nonce received from %s", ip_addr)
                return False

            for query_key, (en_name, es_name) in queries.items():
                # Check display level
                if (
                    (query_key == "temp" and display_level < 1)
                    or (query_key == "batt" and display_level < 2)
                    or (query_key == "sw_port" and display_level < 3)
                    or (query_key == "free" and display_level < 4)
                ):
                    break

                # Prepare and send query
                instring = f"{query_key}{nonce}".encode("utf-8")
                signature = hashlib.sha1(instring).hexdigest()
                payload = f'{{"callType":"{query_key}","parameter":"","signature":"{signature}"}}'
                await ws.send(payload)
                logging.debug("Sent to %s: %s", ip_addr, payload)

                # Receive response
                result = await ws.recv()
                logging.debug("Received from %s: %s", ip_addr, result)
                data = (
                    result.partition('data": "')[2]
                    .partition('", "success')[0]
                    .replace("\\n", " ")
                )

                # Handle MAC filter for first query (gtme_web)
                if query_key == "gtme_web" and mac_filter:
                    if mac_filter.lower() in data.lower():
                        mac_filter_found = True
                    else:
                        return False

                # Print IP address on first valid query
                if query_key == "gtme_web":
                    name = en_name if language == "EN" else es_name
                    print(f"{name}= {ip_addr}")
                    logging.info("Found nGeniusPULSE device at %s", ip_addr)

                # Format and print data
                name = en_name if language == "EN" else es_name
                if query_key == "free":
                    print(f"{name}")
                    data = data.replace(":", "=").replace("kB ", "kB\n").replace("kB", "k")
                elif query_key in ("batt", "poev"):
                    data = data[5:] if len(data) > 5 else data
                    print(f"{name}= {data}")
                else:
                    print(f"{name}= {data}")

                # Update nonce for next query
                nonce = result.partition('nonce": "')[2].partition('", "data')[0]

            return True if not mac_filter or mac_filter_found else False

    except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError, OSError) as err:
        logging.debug("Failed to query %s: %s", ip_addr, err)
        return False


async def scan_network(network, timeout, display_level, language, mac_filter):
    """Scan the network for NetScout nGeniusPULSE devices via WebSocket.

    Args:
        network (str): IPv4 network in CIDR notation.
        timeout (float): Timeout for WebSocket operations.
        display_level (int): Level of information to display (0-9).
        language (str): Language code ("EN" or "ES").
        mac_filter (str): MAC address suffix filter (empty if none).

    Returns:
        int: Number of units found.
    """
    queries = {
        "gtme_web": ("MAC Address", "Dirección MAC"),
        "bver": ("Build Version", "Información de la versión"),
        "temp": ("CPU Temp (degC)", "CPU temperatura (degC)"),
        "link": ("Link Info", "Enlace información"),
        "up_dhm": ("System UpTime", "El tiempo de actividad"),
        "batt": ("Voltage - Battery", "Voltaje - Batería"),
        "poev": ("Voltage - PoE", "Voltaje - PoE"),
        "gurl": ("Gemini Cloud URL", "Gemini Cloud URL"),
        "mach": ("Machine Hardware Name", "Máquina nombre de hardware"),
        "sw_port": ("Nearest Switch - Port", "Conmutador de red - Identificador de puerto"),
        "sw_addr": ("Nearest Switch - IP/MAC", "Conmutador de red - Dirección (IP/MAC)"),
        "sw_name": ("Nearest Switch - Name", "Conmutador de red - Nombre"),
        "free": ("Memory Information...", "Información de la memoria..."),
    }

    num_units_found = 0
    network = ipaddress.ip_network(network, strict=False)
    ip_list = list(network)[1:-1]  # Exclude network and broadcast addresses

    start_time = datetime.now()
    logging.info("Scanning network: %s (%d IPs)", network, len(ip_list))
    print(f"Scan IP Network: {network}")
    print(f"Scan Begin Addr: {ip_list[0]}")
    print(f"Scan End Addr:   {ip_list[-1]}")
    print("")

    tasks = [
        query_device(str(ip), queries, timeout, display_level, language, mac_filter)
        for ip in ip_list
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if result and not isinstance(result, Exception):
            num_units_found += 1

    end_time = datetime.now()
    scan_time = end_time - start_time
    logging.info(
        "Scan completed: %d nGeniusPULSE devices found in %.3fs",
        num_units_found,
        scan_time.total_seconds(),
    )

    return num_units_found


async def main():
    """Main function to coordinate the BigRed WebSocket Client process."""
    args = parse_arguments()
    setup_logging(args.verbose)

    try:
        num_units_found = await scan_network(
            args.network,
            args.timeout,
            args.display_level,
            args.language,
            args.mac_filter,
        )
        print("\nDONE")
        if not args.mac_filter:
            print(f"Total nGeniusPULSE devices found= {num_units_found}")
        logging.info("Total nGeniusPULSE devices found: %d", num_units_found)
    except KeyboardInterrupt:
        logging.info("Scan interrupted by user")
        print("\nScan interrupted")
    except Exception as err:
        logging.error("Unexpected error: %s", err)
        print(f"Error: {err}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())