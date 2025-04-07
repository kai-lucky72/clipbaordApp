# Advanced Clipboard Manager

A cross-platform clipboard manager that tracks your clipboard history and provides quick access to previously copied items. It features GUI, CLI, Quick Paste Popup, Web Interface, and Browser Extension, making it versatile for different environments and user preferences.

![Clipboard Manager](https://raw.githubusercontent.com/kai-lucky72/clipbaordApp/main/browser_extension/images/icon128.svg)

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

## 📋 Quick Start

1. Clone the repository
   ```bash
   git clone https://github.com/kai-lucky72/clipbaordApp.git
   cd clipbaordApp
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the PostgreSQL database
   ```bash
   export DATABASE_URL=postgresql://username:password@localhost:5432/clipboard_db
   ```

4. Start the application (choose one method)
   ```bash
   # GUI interface
   python clipboard_app.py --gui
   
   # Web interface
   python web_app.py
   
   # CLI interface
   python cli_run.py
   
   # Quick Paste Popup
   python clipboard_app.py --popup
   ```

## Requirements

- Python 3.8 or higher
- Dependencies:
  - SQLAlchemy
  - psycopg2-binary (for PostgreSQL support)
  - PostgreSQL database
  - Pillow (for image support)
  - Tkinter (included in standard Python library)
  - Flask (for web interface)
  - PyQt5 (optional, for enhanced GUI features)
  - pyperclip (for clipboard operations)
  - flask-login (for web interface authentication)

## Installation Guide

### Environment Setup

#### Windows

1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
3. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/kai-lucky72/clipbaordApp.git
   cd clipbaordApp
   pip install -r requirements.txt
   ```
4. Set up the database:
   ```bash
   set DATABASE_URL=postgresql://username:password@localhost:5432/clipboard_db
   ```

#### macOS

1. Install Python and PostgreSQL using Homebrew:
   ```bash
   brew install python postgresql
   brew services start postgresql
   ```
2. Clone and set up the application:
   ```bash
   git clone https://github.com/kai-lucky72/clipbaordApp.git
   cd clipbaordApp
   pip3 install -r requirements.txt
   ```
3. Configure the database:
   ```bash
   export DATABASE_URL=postgresql://username:password@localhost:5432/clipboard_db
   ```

#### Linux

1. Install system dependencies:
   ```bash
   # Debian/Ubuntu
   sudo apt update
   sudo apt install python3 python3-pip python3-tk postgresql xclip
   
   # Fedora
   sudo dnf install python3 python3-pip python3-tkinter postgresql xclip
   
   # Arch Linux
   sudo pacman -S python python-pip tk postgresql xclip
   ```
2. Set up PostgreSQL:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   sudo -u postgres createuser --interactive
   sudo -u postgres createdb clipboard_db
   ```
3. Clone and set up the application:
   ```bash
   git clone https://github.com/kai-lucky72/clipbaordApp.git
   cd clipbaordApp
   pip3 install -r requirements.txt
   ```
4. Configure environment:
   ```bash
   export DATABASE_URL=postgresql://username:password@localhost:5432/clipboard_db
   ```

### Docker Installation

1. Build and run using Docker:
   ```bash
   docker-compose up -d
   ```
   This will create and start containers for both the application and the PostgreSQL database.

### Browser Extension Setup

The browser extension enhances the clipboard manager by:
- Silently capturing copied content when you press Ctrl+C
- Showing a Quick Paste popup with recent items when you press Ctrl+V
- Positioning the popup near your cursor for easy selection

To install the browser extension:

1. Start the web interface: `python web_app.py`
2. Open Chrome or any Chromium-based browser
3. Go to Extensions (chrome://extensions/)
4. Enable Developer Mode
5. Click "Load unpacked" button
6. Select the `browser_extension` folder from the repository
7. The extension is now ready to use!

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

## Browser Extension Features

The Browser Extension integrates the Advanced Clipboard Manager with your browser:

- **Silent Copying**: Automatically saves text when you press Ctrl+C without any visual interruption
- **Quick Paste Popup**: Shows 5 recent clipboard items when you press Ctrl+V, positioned near your cursor
- **Seamless Integration**: Works with regular copy-paste operations without disrupting workflow
- **Easy Installation**: Available for Chrome and other Chromium-based browsers
- **Minimal User Interface**: Shows just what you need when you need it

### Extension Usage

1. **Copying content**: 
   - Simply use Ctrl+C as normal - the extension silently saves your copied content
   - No popups or notifications interrupt your workflow

2. **Pasting content**:
   - When you press Ctrl+V, a small popup appears near your cursor
   - The popup shows your 5 most recent clipboard items
   - Click any item to paste it, or continue with default paste if you don't select anything
   - Popup disappears automatically after selection or when you click elsewhere

3. **Additional features**:
   - The extension icon in your toolbar opens a full popup with search capability
   - Link to full web interface for advanced management
   - Context menu options for saving selected text

## Deployment Options

### Render.com Deployment

1. Push your code to GitHub
2. Log in to Render.com
3. Create a new Web Service:
   - Connect your repository
   - Select as Python Application
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `python web_app.py`
   - Add environment variable: `DATABASE_URL`
4. Create a new PostgreSQL database in Render
5. Link the database to your web service

### Heroku Deployment

1. Install Heroku CLI and log in:
   ```bash
   heroku login
   ```
2. Create a Heroku app:
   ```bash
   heroku create advanced-clipboard-manager
   ```
3. Add PostgreSQL addon:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```
4. Push your code:
   ```bash
   git push heroku main
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t clipboard-manager .
   ```
2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## In-Memory Clipboard

In environments where system clipboard tools (like xclip on Linux) are not available, the application uses an in-memory clipboard. This allows you to still save and retrieve clipboard items, although they won't be accessible to other applications until you copy them to the system clipboard.

## Database Configuration

By default, the application uses the PostgreSQL database specified in the `DATABASE_URL` environment variable. If this is not available, it will fall back to a SQLite database.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure PostgreSQL is running: `pg_isready`
   - Verify credentials in DATABASE_URL
   - Check database permissions

2. **Clipboard Access Issues**:
   - On Linux, ensure xclip is installed
   - On macOS, grant terminal access to clipboard in System Preferences
   - On Windows, verify user permissions

3. **GUI Display Problems**:
   - Ensure Tkinter/Qt dependencies are installed
   - Check display settings and permissions

4. **Browser Extension Issues**:
   - Verify web interface is running at http://localhost:5000
   - Check browser extension permissions
   - Ensure the extension has clipboard access permissions

### Getting Help

If you encounter issues, check the logs:
- GUI/CLI: Check console output
- Web Interface: Check browser console and server logs
- Browser Extension: Check browser extension debugging console

## Vercel Deployment

This application can also be deployed on Vercel with the following steps:

1. Fork or push this repository to your GitHub account
2. Log in to [Vercel](https://vercel.com)
3. Create a new project and select your repository
4. Configure the following settings:
   - **Framework Preset**: Other
   - **Build Command**: Leave empty (using vercel.json configuration)
   - **Output Directory**: Leave empty
   - **Install Command**: pip install -r requirements.txt
5. Add the environment variable:
   - `DATABASE_URL`: Your PostgreSQL connection string
6. Click "Deploy"

The Vercel deployment will automatically use the configuration in `vercel.json` which sets up the web app as a serverless function. 

### Notes for Vercel Deployment

- Only the web interface will be deployed on Vercel
- For full functionality, you'll need to set up a PostgreSQL database (you can use Vercel's PostgreSQL integration)
- The clipboard monitoring functionality won't be available in the serverless environment
- For clipboard management features, you should use the browser extension, which will connect to your Vercel deployment

### Vercel + Browser Extension

To use the browser extension with your Vercel deployment:

1. Deploy your application to Vercel using the steps above
2. Edit the browser extension configuration (in `browser_extension/scripts/background.js`) to point to your Vercel URL:
   ```javascript
   const API_BASE_URL = 'https://your-vercel-deployment-url.vercel.app';
   ```
3. Load the extension into your browser as described in the Browser Extension Setup section

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.