// Advanced Clipboard Manager - Popup Script

const API_BASE_URL = 'http://localhost:5000/api';
let clipboardItems = [];

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check connection to server
    checkServerConnection();
    
    // Load clipboard items
    loadClipboardItems();
    
    // Set up search functionality
    document.querySelector('.search-input').addEventListener('input', function(e) {
        const searchText = e.target.value.toLowerCase();
        filterClipboardItems(searchText);
    });
});

// Check connection to clipboard manager server
function checkServerConnection() {
    fetch(`${API_BASE_URL}/status`)
        .then(response => {
            if (response.ok) {
                setConnectionStatus(true);
            } else {
                setConnectionStatus(false);
            }
            return response.json();
        })
        .then(data => {
            console.log('Server status:', data);
        })
        .catch(error => {
            console.error('Server connection error:', error);
            setConnectionStatus(false);
        });
}

// Set connection status indicator
function setConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connection-status');
    
    if (isConnected) {
        statusElement.textContent = '🟢';
        statusElement.title = 'Connected to server';
    } else {
        statusElement.textContent = '🔴';
        statusElement.title = 'Not connected to server';
    }
}

// Load clipboard items from server
function loadClipboardItems() {
    fetch(`${API_BASE_URL}/items/recent?limit=5`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.items) {
                clipboardItems = data.items;
                displayClipboardItems(clipboardItems);
            } else {
                console.error('Failed to load clipboard items:', data.error || 'Unknown error');
                displayError('Failed to load clipboard items');
            }
        })
        .catch(error => {
            console.error('Error loading clipboard items:', error);
            displayError('Could not connect to the server');
        });
}

// Display clipboard items in the popup
function displayClipboardItems(items) {
    const container = document.getElementById('clipboardItems');
    container.innerHTML = '';
    
    if (items.length === 0) {
        container.innerHTML = '<div class="empty-message">No clipboard items found</div>';
        return;
    }
    
    items.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'clipboard-item';
        
        const timeAgo = getTimeAgo(new Date(item.timestamp));
        
        // Format content based on type
        let contentPreview = item.content;
        if (item.type === 'image') {
            contentPreview = '[Image]';
        } else if (contentPreview.length > 60) {
            contentPreview = contentPreview.substring(0, 60) + '...';
        }
        
        // Create HTML structure for the item
        itemElement.innerHTML = `
            <div>
                <div class="item-content">${escapeHtml(contentPreview)}</div>
                <div class="item-time">${timeAgo}</div>
            </div>
            <div class="item-actions">
                <button class="copy-btn" title="Copy">📋</button>
                <button class="delete-btn" title="Delete">🗑️</button>
            </div>
        `;
        
        // Add click event to copy the item
        itemElement.querySelector('.copy-btn').addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent item click
            copyToClipboard(item);
        });
        
        // Add click event to delete the item
        itemElement.querySelector('.delete-btn').addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent item click
            deleteClipboardItem(item.id);
        });
        
        // Add click event to the whole item
        itemElement.addEventListener('click', function() {
            copyToClipboard(item);
        });
        
        container.appendChild(itemElement);
    });
}

// Copy item to clipboard
function copyToClipboard(item) {
    // First try to use the Clipboard API directly
    if (item.type === 'text' && navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(item.content)
            .then(() => {
                showCopySuccess();
            })
            .catch(err => {
                console.error('Failed to write to clipboard:', err);
                // Fall back to background script
                copyViaBackground(item);
            });
    } else {
        // For other types or if direct access fails, use background script
        copyViaBackground(item);
    }
}

// Copy via background script (for images or when direct access fails)
function copyViaBackground(item) {
    chrome.runtime.sendMessage({
        action: 'copyToClipboard',
        text: item.content
    }, function(response) {
        if (response && response.success) {
            showCopySuccess();
        } else {
            console.error('Error copying via background:', response ? response.error : 'Unknown error');
        }
    });
}

// Show copy success indicator
function showCopySuccess() {
    // Flash effect on header to indicate success
    const header = document.querySelector('.header');
    header.classList.add('copy-success');
    
    setTimeout(() => {
        header.classList.remove('copy-success');
    }, 500);
}

// Delete clipboard item
function deleteClipboardItem(itemId) {
    fetch(`${API_BASE_URL}/item/${itemId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload clipboard items
            loadClipboardItems();
        } else {
            console.error('Failed to delete item:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error deleting item:', error);
    });
}

// Filter clipboard items based on search text
function filterClipboardItems(searchText) {
    if (!searchText) {
        displayClipboardItems(clipboardItems);
        return;
    }
    
    const filtered = clipboardItems.filter(item => {
        if (item.type === 'text') {
            return item.content.toLowerCase().includes(searchText);
        }
        return false; // Can't search in images
    });
    
    displayClipboardItems(filtered);
}

// Display error message
function displayError(message) {
    const container = document.getElementById('clipboardItems');
    container.innerHTML = `<div class="error-message">${message}</div>`;
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Get relative time string (e.g., "5 minutes ago")
function getTimeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) {
        return 'Just now';
    }
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    }
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    }
    
    const days = Math.floor(hours / 24);
    if (days < 30) {
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    }
    
    const months = Math.floor(days / 30);
    if (months < 12) {
        return `${months} month${months !== 1 ? 's' : ''} ago`;
    }
    
    const years = Math.floor(months / 12);
    return `${years} year${years !== 1 ? 's' : ''} ago`;
}
