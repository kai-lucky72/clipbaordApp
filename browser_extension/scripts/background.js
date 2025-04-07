// Advanced Clipboard Manager - Background Script

// Set up constants
const API_BASE_URL = 'http://localhost:5000/api';
let lastCopiedText = '';
let isMonitoring = true;

// Initialize on extension install or update
chrome.runtime.onInstalled.addListener(function(details) {
    console.log('Advanced Clipboard Manager extension installed/updated:', details.reason);
    
    // Create context menu items
    chrome.contextMenus.create({
        id: 'save-selection',
        title: 'Save to Clipboard History',
        contexts: ['selection']
    });
    
    // Initialize storage with default settings
    chrome.storage.local.get(['settings'], function(result) {
        if (!result.settings) {
            const defaultSettings = {
                monitorClipboard: true,
                showNotifications: false, // Set to false to avoid showing notifications
                autoConnect: true,
                serverUrl: API_BASE_URL
            };
            
            chrome.storage.local.set({ settings: defaultSettings });
        }
    });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(function(info, tab) {
    if (info.menuItemId === 'save-selection' && info.selectionText) {
        saveTextToClipboard(info.selectionText);
    }
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    switch (request.action) {
        case 'copyToClipboard':
            handleCopyToClipboard(request.text, sendResponse);
            break;
            
        case 'textCopied':
            handleTextCopied(request.text, sendResponse);
            break;
            
        case 'deleteItem':
            deleteClipboardItem(request.itemId, sendResponse);
            break;
            
        case 'getSettings':
            getSettings(sendResponse);
            break;
            
        case 'saveSettings':
            saveSettings(request.settings, sendResponse);
            break;
            
        case 'toggleMonitoring':
            toggleMonitoring(sendResponse);
            break;
    }
    
    // Return true to indicate async response
    return true;
});

// Handle clipboard monitoring
function startClipboardMonitoring() {
    // Check if we have permission to access the clipboard
    navigator.permissions.query({ name: 'clipboard-read' }).then(result => {
        if (result.state === 'granted' || result.state === 'prompt') {
            // Try to set up clipboard monitoring
            setInterval(checkClipboard, 1000);
        } else {
            console.log('Clipboard read permission not granted');
            // We'll rely on content script events instead
        }
    }).catch(err => {
        console.log('Clipboard permissions API not available, using fallback');
        // We'll rely on content script events instead
    });
}

async function checkClipboard() {
    if (!isMonitoring) return;
    
    try {
        const settings = await getSettingsPromise();
        if (!settings.monitorClipboard) return;
        
        const text = await navigator.clipboard.readText();
        
        // If text changed and not empty, save it
        if (text && text !== lastCopiedText) {
            lastCopiedText = text;
            saveTextToClipboard(text);
        }
    } catch (e) {
        // Cannot read clipboard outside of user gesture in some browsers
        // We'll rely on the content script events instead
    }
}

// Helper functions
function handleCopyToClipboard(text, sendResponse) {
    // Copy to system clipboard
    navigator.clipboard.writeText(text).then(() => {
        lastCopiedText = text; // Update last copied text
        sendResponse({ success: true });
    }).catch(err => {
        console.error('Could not copy text: ', err);
        sendResponse({ success: false, error: err.message });
    });
    
    // Also save to clipboard history silently
    saveTextToClipboard(text);
}

function handleTextCopied(text, sendResponse) {
    if (text && text.trim() && isMonitoring) {
        saveTextToClipboard(text);
    }
    
    if (sendResponse) {
        sendResponse({ success: true });
    }
}

function saveTextToClipboard(text) {
    if (!text || !text.trim()) return;
    
    fetch(`${API_BASE_URL}/items/add`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Successfully saved, but don't show notifications
            console.log('Text saved to clipboard history, ID:', data.item_id);
        }
    })
    .catch(error => {
        console.error('Error saving to clipboard history:', error);
    });
}

function deleteClipboardItem(itemId, sendResponse) {
    fetch(`${API_BASE_URL}/item/${itemId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sendResponse({ success: true });
        } else {
            sendResponse({ success: false, error: data.error || 'Failed to delete item' });
        }
    })
    .catch(error => {
        console.error('Error deleting clipboard item:', error);
        sendResponse({ success: false, error: error.message });
    });
}

function getSettings(sendResponse) {
    chrome.storage.local.get(['settings'], function(result) {
        const settings = result.settings || {
            monitorClipboard: true,
            showNotifications: false, // No notifications
            autoConnect: true,
            serverUrl: API_BASE_URL
        };
        
        sendResponse({ settings });
    });
}

function getSettingsPromise() {
    return new Promise((resolve, reject) => {
        chrome.storage.local.get(['settings'], function(result) {
            const settings = result.settings || {
                monitorClipboard: true,
                showNotifications: false, // No notifications
                autoConnect: true,
                serverUrl: API_BASE_URL
            };
            
            resolve(settings);
        });
    });
}

function saveSettings(settings, sendResponse) {
    chrome.storage.local.set({ settings }, function() {
        sendResponse({ success: true });
    });
}

function toggleMonitoring(sendResponse) {
    isMonitoring = !isMonitoring;
    sendResponse({ isMonitoring });
}

// Start clipboard monitoring if possible
startClipboardMonitoring();

// Listen for keyboard shortcuts
chrome.commands.onCommand.addListener((command) => {
    if (command === "paste_clipboard") {
        // This will be triggered when the user presses the paste shortcut (Ctrl+Shift+V)
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "showQuickPaste"});
        });
    }
});
