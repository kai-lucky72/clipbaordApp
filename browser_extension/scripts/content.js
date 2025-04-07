// Advanced Clipboard Manager - Content Script

// Constants
const API_BASE_URL = 'http://localhost:5000/api';
let quickPastePopup = null;
let recentItems = [];
let lastCopyEvent = null;

// Listen for keyboard events
document.addEventListener('keydown', function(event) {
    // Check for Ctrl+C (copy event)
    if (event.ctrlKey && event.code === 'KeyC') {
        handleCopyEvent();
    }
    
    // Check for Ctrl+V (paste event) - to show quick paste popup
    if (event.ctrlKey && event.code === 'KeyV') {
        handlePasteEvent(event);
    }
});

// Listen for messages from the background script
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'showQuickPaste') {
        showQuickPastePopup();
        sendResponse({success: true});
    }
    
    return true; // Indicate async response
});

// Handle copy event
function handleCopyEvent() {
    // Capture the selected text
    const selectedText = window.getSelection().toString();
    
    if (selectedText && selectedText.trim()) {
        // Save the selected text to clipboard history via background script
        chrome.runtime.sendMessage({
            action: 'textCopied',
            text: selectedText
        });
        
        // Save the copy event details for potential paste popup later
        lastCopyEvent = {
            timestamp: Date.now(),
            position: getCurrentCursorPosition()
        };
    }
}

// Handle paste event
function handlePasteEvent(event) {
    // We don't preventDefault because we want the normal paste to still occur
    // if the user doesn't select from our popup
    
    // Show quick paste popup near the cursor
    showQuickPastePopup();
}

// Show quick paste popup
function showQuickPastePopup() {
    // First load the recent items
    loadRecentItems(function() {
        // Get current cursor position
        const cursorPos = getCurrentCursorPosition();
        
        // Create and show the popup
        createQuickPastePopup(cursorPos);
    });
}

// Load recent clipboard items
function loadRecentItems(callback) {
    fetch(`${API_BASE_URL}/items/recent?limit=5`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.items) {
                recentItems = data.items;
            } else {
                console.error('Error loading recent items:', data.error || 'Unknown error');
                recentItems = [];
            }
            
            if (callback) callback();
        })
        .catch(error => {
            console.error('Failed to load recent items:', error);
            recentItems = [];
            
            if (callback) callback();
        });
}

// Create and show the quick paste popup
function createQuickPastePopup(position) {
    // Remove existing popup if it exists
    removeQuickPastePopup();
    
    // Create the popup container
    quickPastePopup = document.createElement('div');
    quickPastePopup.id = 'acm-quick-paste-popup';
    quickPastePopup.style.cssText = `
        position: fixed;
        z-index: 9999999;
        background-color: white;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        max-width: 300px;
        width: 300px;
        font-family: sans-serif;
        font-size: 14px;
        top: ${position.y}px;
        left: ${position.x}px;
        overflow: hidden;
    `;
    
    // Create the header
    const header = document.createElement('div');
    header.style.cssText = `
        padding: 8px 12px;
        background-color: #2c3e50;
        color: white;
        font-weight: bold;
        font-size: 12px;
        border-bottom: 1px solid #ddd;
    `;
    header.textContent = 'Quick Paste';
    quickPastePopup.appendChild(header);
    
    // Create the items container
    const itemsContainer = document.createElement('div');
    itemsContainer.style.cssText = `
        max-height: 200px;
        overflow-y: auto;
    `;
    
    // Add items or message if no items
    if (recentItems.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.style.cssText = `
            padding: 10px 12px;
            color: #666;
            text-align: center;
            font-style: italic;
        `;
        emptyMessage.textContent = 'No recent clipboard items';
        itemsContainer.appendChild(emptyMessage);
    } else {
        recentItems.forEach((item, index) => {
            const itemElement = document.createElement('div');
            itemElement.style.cssText = `
                padding: 8px 12px;
                border-bottom: 1px solid #eee;
                cursor: pointer;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            `;
            itemElement.onmouseover = function() {
                this.style.backgroundColor = '#f0f0f0';
            };
            itemElement.onmouseout = function() {
                this.style.backgroundColor = 'transparent';
            };
            
            // Format content
            let displayContent = '';
            if (item.type === 'image') {
                displayContent = '[Image]';
            } else {
                displayContent = item.content;
                if (displayContent.length > 40) {
                    displayContent = displayContent.substring(0, 40) + '...';
                }
            }
            
            itemElement.textContent = displayContent;
            
            // Set click handler
            itemElement.onclick = function() {
                pasteItemFromPopup(item);
            };
            
            itemsContainer.appendChild(itemElement);
        });
    }
    
    quickPastePopup.appendChild(itemsContainer);
    
    // Create the footer
    const footer = document.createElement('div');
    footer.style.cssText = `
        padding: 6px 12px;
        background-color: #f5f5f5;
        border-top: 1px solid #ddd;
        text-align: center;
        font-size: 11px;
    `;
    
    const link = document.createElement('a');
    link.href = 'http://localhost:5000';
    link.target = '_blank';
    link.textContent = 'Open Clipboard Manager';
    link.style.cssText = `
        color: #3498db;
        text-decoration: none;
    `;
    footer.appendChild(link);
    quickPastePopup.appendChild(footer);
    
    // Add the popup to the page
    document.body.appendChild(quickPastePopup);
    
    // Position the popup near cursor but ensure it's visible
    repositionPopup();
    
    // Add click listener to close popup when clicking outside
    setTimeout(() => {
        document.addEventListener('click', documentClickHandler);
    }, 100);
}

// Reposition popup to ensure it's visible in the viewport
function repositionPopup() {
    if (!quickPastePopup) return;
    
    const rect = quickPastePopup.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Check if popup overflows to the right
    if (rect.right > viewportWidth) {
        quickPastePopup.style.left = (viewportWidth - rect.width - 10) + 'px';
    }
    
    // Check if popup overflows to the bottom
    if (rect.bottom > viewportHeight) {
        quickPastePopup.style.top = (viewportHeight - rect.height - 10) + 'px';
    }
}

// Handle document click to close popup
function documentClickHandler(e) {
    if (quickPastePopup && !quickPastePopup.contains(e.target)) {
        removeQuickPastePopup();
    }
}

// Remove the quick paste popup
function removeQuickPastePopup() {
    if (quickPastePopup && quickPastePopup.parentNode) {
        quickPastePopup.parentNode.removeChild(quickPastePopup);
        quickPastePopup = null;
        
        // Remove the click listener
        document.removeEventListener('click', documentClickHandler);
    }
}

// Paste an item from the popup
function pasteItemFromPopup(item) {
    // Copy the item to clipboard via background script
    chrome.runtime.sendMessage({
        action: 'copyToClipboard',
        text: item.content
    }, function(response) {
        if (response && response.success) {
            // Remove popup after selection
            removeQuickPastePopup();
            
            // Try to simulate a paste action
            simulatePaste();
        }
    });
}

// Try to simulate a paste action
function simulatePaste() {
    // This is tricky because browser security restrictions don't allow
    // simulating paste directly in many contexts
    
    // Focus on active element and try to dispatch a paste event
    const activeElement = document.activeElement;
    
    if (activeElement) {
        try {
            // Try to create and dispatch a paste event
            const pasteEvent = new ClipboardEvent('paste', {
                bubbles: true,
                cancelable: true,
                clipboardData: new DataTransfer()
            });
            
            activeElement.dispatchEvent(pasteEvent);
        } catch (e) {
            console.log('Paste simulation failed, user will need to press Ctrl+V again');
        }
    }
}

// Helper function to get current cursor/caret position
function getCurrentCursorPosition() {
    let x = 0;
    let y = 0;
    
    // Try to use last known copy event position
    if (lastCopyEvent && Date.now() - lastCopyEvent.timestamp < 5000) {
        return lastCopyEvent.position;
    }
    
    // Try to get selection coordinates
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const rects = range.getClientRects();
        
        if (rects.length > 0) {
            const rect = rects[0];
            x = rect.right;
            y = rect.bottom + 10; // Position below the selection
            
            return { x, y };
        }
    }
    
    // Fallback to current active element
    const activeElement = document.activeElement;
    if (activeElement) {
        const rect = activeElement.getBoundingClientRect();
        x = rect.left;
        y = rect.bottom;
        
        return { x, y };
    }
    
    // Fallback to mouse position or center of screen
    if (typeof mouseX !== 'undefined' && typeof mouseY !== 'undefined') {
        return { x: mouseX, y: mouseY };
    } else {
        return { 
            x: window.innerWidth / 2 - 150, 
            y: window.innerHeight / 3 
        };
    }
}

// Track mouse position as a fallback for cursor position
let mouseX = 0;
let mouseY = 0;
document.addEventListener('mousemove', function(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
});

// Initialize
console.log('Advanced Clipboard Manager content script initialized');
