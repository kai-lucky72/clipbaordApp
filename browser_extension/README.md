# Advanced Clipboard Manager - Browser Extension

A powerful browser extension for the Advanced Clipboard Manager that allows you to access and manage your clipboard history directly from your browser.

## Features

- **View Clipboard History**: Access your entire clipboard history from your browser
- **Search & Filter**: Find specific clipboard items quickly
- **Context Menu Integration**: Save selected text directly to your clipboard history
- **Copy & Paste**: Copy or paste items with a single click
- **Favorites**: Mark frequently used items as favorites for quick access
- **Tags**: Organize clipboard items with custom tags
- **Code Highlighting**: Syntax highlighting for code snippets
- **Keyboard Shortcuts**: Quick access with keyboard shortcuts
- **Responsive Interface**: Modern, responsive design that works across devices

## Installation

### Prerequisites

- The Advanced Clipboard Manager application must be running with the Web Interface active (port 5000)
- Chrome or a Chromium-based browser (Edge, Brave, Opera, etc.)

### Installation Steps

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" by toggling the switch in the top-right corner
3. Click on "Load unpacked" button
4. Select the `browser_extension` folder
5. The extension should now be installed and visible in your browser toolbar

## Usage

### Basic Usage

1. Click the extension icon in your browser toolbar to open the main interface
2. Browse your clipboard history
3. Click on any item to see its full content in the preview panel
4. Use the action buttons to copy, paste, favorite, tag, or delete items

### Advanced Features

- **Search**: Use the search bar to find specific clipboard content
- **Filtering**: Filter items by type (text/image) or favorite status
- **Tagging**: Add tags to organize your clipboard items
- **Direct Input**: Add text directly to clipboard history without copying it first

### Keyboard Shortcuts

- Press `Ctrl+Shift+C` (or `Cmd+Shift+C` on Mac) to open the extension popup
- Within the popup, use arrow keys to navigate items and Enter to select

### Context Menu

- Right-click on any selected text on a web page
- Choose "Save to Clipboard History" to add the text to your clipboard history
- Choose "Show Recent Items" to open the extension popup

## Settings

The extension provides several configurable settings:

- **Monitor Clipboard**: Automatically track clipboard changes while browsing
- **Show Notifications**: Display notifications when items are added to clipboard history
- **Auto-Connect to Server**: Automatically connect to the clipboard manager server on startup
- **Server URL**: Configure the URL of the clipboard manager server

To access settings:
1. Open the extension popup
2. Click on the settings icon in the top-right corner

## Technical Information

### Architecture

The extension consists of:

1. **Background Script**: Monitors the clipboard and manages communication with the server
2. **Content Script**: Interacts with web pages for selecting text and pasting
3. **Popup UI**: The main interface for viewing and managing clipboard items

### Security

The extension requires several permissions:

- `clipboardRead` and `clipboardWrite`: To access and modify the clipboard
- `storage`: To store extension settings
- `contextMenus`: To add right-click menu options
- `host permissions for localhost:5000`: To communicate with the clipboard manager server

### API Integration

The extension communicates with the Advanced Clipboard Manager server using a REST API.

## Troubleshooting

If you experience issues:

1. Ensure the Advanced Clipboard Manager application is running with Web Interface active
2. Check that the server is accessible at http://localhost:5000
3. Verify that your browser's extension settings allow the necessary permissions
4. Restart the browser if changes don't take effect

## License

This extension is part of the Advanced Clipboard Manager project and is subject to the same license terms.

## Further Information

For more detailed information, see:

- [Extension Documentation](EXTENSION.md): Detailed technical documentation
- [Examples](examples/README.md): Code examples and reference materials
- [Main Project README](../README.md): Information about the full application
