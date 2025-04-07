#!/usr/bin/env python3
"""
Advanced Clipboard Manager - Main Entry Point

This script serves as the entry point for the clipboard manager application,
allowing users to choose between CLI and GUI modes.
"""
import sys
import logging
import argparse
from utils import setup_logger

# Configure logging
setup_logger()
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Advanced Clipboard Manager")
    parser.add_argument("--cli", action="store_true", help="Run in command-line interface mode")
    parser.add_argument("--gui", action="store_true", help="Run in graphical user interface mode")
    parser.add_argument("--popup", action="store_true", help="Show quick paste popup window")
    parser.add_argument("--monitor", action="store_true", help="Start clipboard monitoring on startup (CLI mode)")
    parser.add_argument("--recent", type=int, help="Display N most recent clipboard items and exit (CLI mode)")
    return parser.parse_args()

def main():
    """Application entry point"""
    # Parse top-level arguments for this script
    args = parse_arguments()
    
    # Handle popup mode first since it's a specialized mode
    if args.popup:
        logger.info("Starting in Quick Paste Popup mode")
        try:
            import quick_paste_popup
            return quick_paste_popup.main()
        except ImportError as e:
            logger.error(f"Failed to import Quick Paste Popup: {e}")
            print("Error: Quick Paste Popup not available.")
            # Fall back to GUI mode
            args.gui = True
    
    # Default to GUI mode if no mode is specified
    if not args.cli and not args.gui:
        args.gui = True
    
    try:
        # Run in CLI mode
        if args.cli:
            logger.info("Starting in CLI mode")
            
            # Import CLI module
            import main as cli_main
            
            # Prepare CLI arguments
            # Remove any args that are specific to this wrapper script
            sys_args = sys.argv[1:]
            if "--cli" in sys_args:
                sys_args.remove("--cli")
            if "--gui" in sys_args:
                sys_args.remove("--gui")
            if "--popup" in sys_args:
                sys_args.remove("--popup")
                
            # Set up remaining args for CLI
            if sys_args:
                # Replace sys.argv with filtered arguments
                old_argv = sys.argv
                sys.argv = [old_argv[0]] + sys_args
            
            # Run CLI application
            return cli_main.main()
        
        # Run in GUI mode
        elif args.gui:
            logger.info("Starting in GUI mode")
            
            # Try to import Tkinter GUI module
            try:
                import tkinter_gui
                
                # Run Tkinter GUI application
                return tkinter_gui.main()
            except ImportError as e:
                logger.error(f"Failed to import Tkinter GUI: {e}")
                print("Error: Tkinter GUI not available.")
                print("Falling back to CLI mode...")
                
                # Fall back to CLI mode
                import main as cli_main
                return cli_main.main()
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"Error: Required module not found: {e}")
        return 1
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())