# Browser Extension Examples

This directory contains examples and reference materials for working with the Advanced Clipboard Manager browser extension.

## Contents

- `api_interaction.js`: Demonstrates how to interact with the Clipboard Manager API from JavaScript
- `firefox/`: Contains examples for Firefox-specific adaptation of the extension

## Using the API Interaction Examples

The `api_interaction.js` file contains several functions demonstrating how to:

1. Retrieve clipboard items
2. Add text to clipboard history
3. Toggle favorite status
4. Search clipboard history
5. Add tags to items
6. Delete items
7. Check server status
8. Retrieve system information

These examples can be incorporated into your own scripts or extensions as needed.

## Cross-Browser Support

While the extension currently targets Chrome and Chromium-based browsers, the examples in the `firefox/` directory show how to adapt it for Firefox.

Key differences for Firefox:

1. Uses manifest v2 instead of v3
2. Replaces service worker with background script
3. Uses browser_action instead of action
4. Modifies permissions format

For other browsers, similar adaptations may be necessary based on their extension APIs.
