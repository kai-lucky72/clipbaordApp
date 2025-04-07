# Advanced Clipboard Manager - Browser Extension

A powerful browser extension for the Advanced Clipboard Manager that allows you to access and manage your clipboard history directly from your browser.

## Features

- **Seamless Clipboard Integration**: Automatically saves anything you copy (Ctrl+C) without disrupting your workflow
- **Quick Paste Popup**: Press Ctrl+V to see a small popup with your 5 most recent clipboard items
- **Smart Positioning**: The popup appears near your cursor for easy selection
- **Multi-Content Support**: Works with text, code snippets, and images
- **Simple Interface**: Minimal UI shows just what you need when you need it
- **Link to Full Application**: Access the full web interface when needed

## How It Works

1. **When you press Ctrl+C**: The extension silently saves your copied content to the clipboard history without showing any notifications or popups, allowing you to continue working without interruption.

2. **When you press Ctrl+V**: 
   - A small popup appears near your cursor with your 5 most recent clipboard items
   - Select any item to paste it into the current field
   - Continue with the standard paste operation if you don't select an item
   - The popup disappears after pasting or when you click elsewhere

3. **Need More Options?**: The popup includes a link to the full web interface where you can manage your entire clipboard history, add tags, search, etc.

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

## Keyboard Shortcuts

- **Ctrl+C**: Copy and silently save to clipboard history (standard copy behavior)
- **Ctrl+V**: Show the quick paste popup with your 5 most recent items (alongside standard paste)
- **Ctrl+Shift+C**: Open the full extension popup for advanced management
- **Ctrl+Shift+V**: Explicitly trigger the quick paste popup (alternative)

## Usage Tips

- The extension works best when the Advanced Clipboard Manager server is running in the background
- Multiple consecutive copies are all saved automatically
- When pasting, the popup shows only the 5 most recent items for quick access
- For older items, use the full web interface accessible from the popup's bottom link

## Technical Information

The extension requires these permissions:
- `clipboardRead` and `clipboardWrite`: To access and modify the clipboard
- `storage`: To store extension settings
- `contextMenus`: To add right-click menu options
- `host permissions for localhost:5000`: To communicate with the clipboard manager server

## Troubleshooting

If you experience issues:

1. Ensure the Advanced Clipboard Manager application is running with Web Interface active
2. Check that the server is accessible at http://localhost:5000
3. Verify that your browser's extension settings allow the necessary permissions
4. Restart the browser if changes don't take effect

## License

This extension is part of the Advanced Clipboard Manager project and is subject to the same license terms.
