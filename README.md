# Advanced Clipboard Manager (CLI Edition)

A cross-platform clipboard manager that tracks your clipboard history and provides quick access to previously copied items. This CLI edition is designed to work in environments where GUI applications might not be available.

## Features

- **Clipboard Monitoring**: Continuously tracks text copied to your clipboard
- **Database Storage**: Stores clipboard history in a PostgreSQL database
- **Interactive CLI**: Easy-to-use command-line interface
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Favorites**: Mark frequently used items as favorites for quick access
- **Search Functionality**: Quickly find items in your clipboard history
- **Tagging System**: Organize clipboard items with custom tags

## Requirements

- Python 3.8 or higher
- SQLAlchemy
- psycopg2-binary (for PostgreSQL support)
- PostgreSQL database

## Usage

### Starting the Application

```bash
python main.py
```

### Command-line Arguments

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

## Future Features

The following features are planned for future releases:

- **Image Support**: Store and retrieve images from the clipboard
- **Encryption**: End-to-end encryption of sensitive clipboard data
- **Browser Extension**: Seamless integration with web browsers
- **Cloud Synchronization**: Sync clipboard history across multiple devices
- **GUI Interface**: A graphical user interface for desktop environments
- **Custom Categories**: Organize clipboard items beyond simple tags
- **Export/Import**: Export and import clipboard history

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
