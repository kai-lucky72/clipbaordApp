# Browser Extension Integration

The Advanced Clipboard Manager Browser Extension provides seamless integration between your browser and the clipboard manager application. This document explains how to use and extend the extension for different browsers.

## Supported Browsers

The extension currently supports:

- Google Chrome
- Microsoft Edge
- Brave Browser
- Opera
- Any other Chromium-based browser

## Installation Instructions

### Chrome/Edge/Brave/Opera

1. Open Chrome and navigate to `chrome://extensions/` (or equivalent in your browser)
2. Enable "Developer mode" by toggling the switch in the top-right corner
3. Click on "Load unpacked" button
4. Select the `browser_extension` folder
5. The extension should now be installed and visible in your browser toolbar

### Firefox (Future Support)

Currently, the extension does not support Firefox, but it could be adapted with the following steps:

1. Modify the manifest.json file to use the Firefox extension format (manifest_version 2)
2. Replace Chrome-specific APIs with Firefox equivalents
3. Replace the background service worker with a background script
4. Test and adapt as needed

## Using the Extension

### Basic Usage

- Click on the extension icon to view your clipboard history
- Use the search bar to find specific items
- Filter items by type or favorites status
- Click on an item to see its full content in the preview panel
- Use the buttons to copy, paste, favorite, tag, or delete items

### Context Menu Integration

- Right-click on any selected text on a web page
- Choose "Save to Clipboard History" to add the text to your clipboard history
- Choose "Show Recent Items" to open the extension popup

### Keyboard Shortcuts

- Press `Ctrl+Shift+C` (or `Cmd+Shift+C` on Mac) to open the extension popup
- Press `Ctrl+Shift+V` to open the quick paste popup (if implemented)

## Extension Architecture

The extension consists of several key components:

1. **Manifest.json**: Defines the extension's permissions, components, and metadata
2. **Background Script**: Manages clipboard monitoring and communication with the server
3. **Content Script**: Interacts with web pages to get selected text and handle paste operations
4. **Popup Interface**: Provides the UI for viewing and managing clipboard items
5. **Settings Page**: Allows configuration of extension behavior

## API Integration

The extension communicates with the Advanced Clipboard Manager server using a REST API. The key endpoints include:

- `/api/items`: Get clipboard items with filtering and pagination
- `/api/item/{id}`: Get details for a specific item
- `/api/item/{id}/favorite`: Toggle favorite status
- `/api/item/{id}/tags`: Manage item tags
- `/api/items/add`: Add new text to clipboard history
- `/api/ping`: Check if the server is available
- `/api/system/info`: Get system information
- `/api/extension/copy`: Copy text from the extension to the clipboard and database

## Extension Settings

The extension provides several configurable settings:

- **Monitor Clipboard**: Automatically track clipboard changes while browsing
- **Show Notifications**: Display notifications when items are added to clipboard history
- **Auto-Connect to Server**: Automatically connect to the clipboard manager server on startup
- **Server URL**: Configure the URL of the clipboard manager server

## Customization and Development

### Custom Icon

To use a custom icon:

1. Replace the icon files in the `images` directory
2. Ensure you provide all required sizes (16x16, 48x48, 128x128)

### Custom Styles

To customize the appearance:

1. Modify the CSS files in the `styles` directory
2. Test your changes to ensure compatibility across browsers

### Adding New Features

To extend the extension with new features:

1. Modify the relevant files (background.js, content.js, popup.js)
2. Update the manifest.json file if needed (for new permissions or components)
3. Test thoroughly across different browsers

## Troubleshooting

If you encounter issues with the extension:

- Ensure the Advanced Clipboard Manager server is running and accessible
- Check the browser console for error messages
- Verify that your browser's extension settings allow the necessary permissions
- Try restarting the browser if changes don't take effect

## Security Notes

The extension requires several permissions to function correctly:

- `clipboardRead` and `clipboardWrite`: To access and modify the clipboard
- `storage`: To store extension settings
- `contextMenus`: To add right-click menu options
- `host permissions for localhost:5000`: To communicate with the clipboard manager server

These permissions are necessary for core functionality but should be reviewed for security implications.

## Contributing

Contributions to the browser extension are welcome! If you'd like to improve the extension or add support for additional browsers, please submit a pull request or open an issue for discussion.
