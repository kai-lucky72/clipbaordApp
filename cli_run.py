#!/usr/bin/env python3
"""
CLI Runner for Advanced Clipboard Manager

This is a simple wrapper to start the CLI version of the clipboard manager.
"""
import sys
import main as cli_main

if __name__ == "__main__":
    # Run the CLI application
    sys.exit(cli_main.main())