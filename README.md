# Advanced Clipboard Manager

A cross-platform clipboard manager that tracks your clipboard history and provides quick access to previously copied items. It features GUI, CLI, Quick Paste Popup, Web Interface, and Browser Extension, making it versatile for different environments and user preferences.

## Features

- **Clipboard Monitoring**: Continuously tracks text and images copied to your clipboard
- **Database Storage**: Stores clipboard history in a PostgreSQL database
- **Multiple Interfaces**: GUI, CLI, Quick Paste Popup, Web Interface, and Browser Extension
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Favorites**: Mark frequently used items as favorites for quick access
- **Search Functionality**: Quickly find items in your clipboard history
- **Tagging System**: Organize clipboard items with custom tags
- **Image Support**: Store, view, and save images from your clipboard
- **Preview Panel**: Preview text and images before copying
- **Quick Paste Popup**: Access recent clipboard items through a lightweight popup interface
- **Web Interface**: Access your clipboard history through a browser
- **Browser Extension**: Seamless integration with Chrome and Chromium-based browsers

## Requirements

- Python 3.8 or higher
- SQLAlchemy
- psycopg2-binary (for PostgreSQL support)
- PostgreSQL database
- Pillow (for image support)
- Tkinter (included in standard Python library)
- Flask (for web interface)

## Usage

### Starting the Application

```bash
# Start with the default GUI interface
python clipboard_app.py

# Start specifically in GUI mode
python clipboard_app.py --gui

# Start in CLI mode
python clipboard_app.py --cli

# Start the Quick Paste Popup
python clipboard_app.py --popup

# Start the Web Interface
python web_app.py
```

### Running the CLI Directly

```bash
python cli_run.py
```

### Command-line Arguments

When using the CLI mode:
- `--monitor`: Start clipboard monitoring on startup
- `--recent N`: Display N most recent clipboard items and exit

### Interactive Commands

Once the application is running, the following commands are available:

- `help`: Show available commands
- `start`: Start clipboard monitoring
- `stop`: Stop clipboard monitoring
- `recent [n]`: Show recent clipboard items (default 5)
- `search <text>`: Search clipboard history
- `add <text>`: Add text directly to clipboard history
- `copy <id>`: Copy item with ID to clipboard
- `favorite <id>`: Toggle favorite status for item
- `delete <id>`: Delete item from history
- `clear`: Clear clipboard history (keeps favorites)
- `exit`: Exit the application

### Example Usage

```
# Start clipboard monitoring
clipboard> start

# Add text manually to clipboard
clipboard> add This is a test clipboard item

# View recent clipboard items
clipboard> recent 3

# Search for specific text
clipboard> search test

# Mark an item as favorite
clipboard> favorite 2

# Copy an item to clipboard
clipboard> copy 2

# Exit the application
clipboard> exit
```

## Quick Paste Popup

The Quick Paste Popup provides instant access to your most recent clipboard items:

- Trigger with a keyboard shortcut (Ctrl+Shift+V by default)
- Lightweight interface that appears near your cursor
- Shows the most recent clipboard items
- Click an item to paste it
- Right-click to see additional options (delete, favorite)
- Keyboard navigation supported

To use the Quick Paste Popup as a standalone application:

```bash
python clipboard_app.py --popup
```

## Web Interface

The Web Interface provides browser-based access to your clipboard history:

- Access from any device with a web browser
- Modern, responsive design
- Full clipboard history browsing and management
- Search and filter capabilities
- Tag management with category tags
- Syntax highlighting for code snippets
- Direct text input feature

To start the web interface:

```bash
python web_app.py
```

Then navigate to `http://localhost:5000` in your web browser.

## Browser Extension

The Browser Extension integrates the Advanced Clipboard Manager with your browser:

- Available for Chrome and other Chromium-based browsers (Edge, Brave, Opera)
- Save selected text from web pages to clipboard history
- Paste clipboard items directly into web forms
- Access and manage your clipboard history without leaving the browser
- Tag and favorite management
- Syntax highlighting for code snippets

To install the browser extension:

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" by toggling the switch in the top-right corner
3. Click on "Load unpacked" button
4. Select the `browser_extension` folder
5. Ensure the Advanced Clipboard Manager app is running with the web interface active

## In-Memory Clipboard

In environments where system clipboard tools (like xclip on Linux) are not available, the application uses an in-memory clipboard. This allows you to still save and retrieve clipboard items, although they won't be accessible to other applications until you copy them to the system clipboard.

## Database Configuration

By default, the application uses the PostgreSQL database specified in the `DATABASE_URL` environment variable. If this is not available, it will fall back to a SQLite database.

## Advanced Search Features

The clipboard manager includes robust search capabilities:

- **Text Search**: Find any text in your clipboard history
- **Database Optimization**: Efficiently searches binary data in PostgreSQL
- **Fallback Support**: Works with both PostgreSQL and SQLite databases
- **Case Insensitive**: Searches are case insensitive for easier matching

## GUI Interface

The GUI interface provides a user-friendly way to interact with your clipboard history:

- **Preview Panel**: View text and image content before copying
- **Filter Options**: Filter by content type (text, images) or favorites
- **Search Box**: Quickly find specific content
- **Context Menu**: Right-click on items for additional options
- **Image Handling**: View, copy, and save images from your clipboard
- **Favorites**: Mark frequently used items with a star for easy access
- **Tagging System**: Organize your clipboard items with custom tags

### GUI Controls

- **Menu Bar**: Access application functions and settings
- **Filter Dropdown**: Filter clipboard items by type or favorite status
- **Search Field**: Search for specific text in clipboard history
- **Item List**: Browse and select clipboard items
- **Preview Panel**: Preview the content of selected items
- **Action Buttons**: Copy, delete, or favorite selected items
- **Tag Management**: Add, remove, and filter by tags

## Future Features

The following features are planned for future releases:

- **Encryption**: End-to-end encryption of sensitive clipboard data
- **Cloud Synchronization**: Sync clipboard history across multiple devices
- **Custom Categories**: Organize clipboard items beyond simple tags
- **Export/Import**: Export and import clipboard history
- **Hotkey Support**: Customizable keyboard shortcuts

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
