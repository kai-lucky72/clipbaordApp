// Advanced Clipboard Manager - API Interaction Examples
// This file demonstrates how to interact with the Clipboard Manager API from JavaScript

// Base URL for API
const API_BASE_URL = 'http://localhost:5000/api';

/**
 * Example 1: Get recent clipboard items
 * Retrieves the most recent clipboard items
 */
async function getRecentItems(limit = 5) {
    try {
        const response = await fetch(`${API_BASE_URL}/items?per_page=${limit}`);
        const data = await response.json();
        console.log('Recent items:', data.items);
        return data.items;
    } catch (error) {
        console.error('Error fetching recent items:', error);
        return [];
    }
}

/**
 * Example 2: Add text to clipboard history
 * Adds text to the clipboard history
 */
async function addTextToClipboard(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/items/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('Text added successfully, item ID:', data.item_id);
            return data.item_id;
        } else {
            console.error('Failed to add text:', data.error);
            return null;
        }
    } catch (error) {
        console.error('Error adding text to clipboard:', error);
        return null;
    }
}

/**
 * Example 3: Toggle favorite status of an item
 * Marks or unmarks an item as favorite
 */
async function toggleFavorite(itemId) {
    try {
        const response = await fetch(`${API_BASE_URL}/item/${itemId}/favorite`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('Favorite status updated to:', data.favorite);
            return data.favorite;
        } else {
            console.error('Failed to toggle favorite status:', data.error);
            return null;
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
        return null;
    }
}

/**
 * Example 4: Search clipboard history
 * Searches for items containing specific text
 */
async function searchClipboard(searchText) {
    try {
        const response = await fetch(`${API_BASE_URL}/items?search=${encodeURIComponent(searchText)}`);
        const data = await response.json();
        console.log(`Found ${data.total} items matching "${searchText}"`);
        return data.items;
    } catch (error) {
        console.error('Error searching clipboard:', error);
        return [];
    }
}

/**
 * Example 5: Add a tag to an item
 * Tags an item for better organization
 */
async function addTagToItem(itemId, tag) {
    try {
        const response = await fetch(`${API_BASE_URL}/item/${itemId}/tags`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tag })
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('Tag added, current tags:', data.tags);
            return data.tags;
        } else {
            console.error('Failed to add tag:', data.error);
            return null;
        }
    } catch (error) {
        console.error('Error adding tag:', error);
        return null;
    }
}

/**
 * Example 6: Delete an item
 * Removes an item from clipboard history
 */
async function deleteItem(itemId) {
    try {
        const response = await fetch(`${API_BASE_URL}/item/${itemId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('Item deleted successfully');
            return true;
        } else {
            console.error('Failed to delete item:', data.error);
            return false;
        }
    } catch (error) {
        console.error('Error deleting item:', error);
        return false;
    }
}

/**
 * Example 7: Check server status
 * Verifies if the Clipboard Manager server is running
 */
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/ping`);
        const data = await response.json();
        
        if (data.success) {
            console.log('Server is running:', data.message);
            console.log('Server timestamp:', data.timestamp);
            return true;
        } else {
            console.error('Server returned unexpected response');
            return false;
        }
    } catch (error) {
        console.error('Server is not accessible:', error);
        return false;
    }
}

/**
 * Example 8: Get system information
 * Retrieves information about the clipboard manager system
 */
async function getSystemInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/system/info`);
        const data = await response.json();
        
        if (data.success) {
            console.log('System stats:', data.stats);
            console.log('Server info:', data.server_info);
            return data;
        } else {
            console.error('Failed to get system info');
            return null;
        }
    } catch (error) {
        console.error('Error getting system info:', error);
        return null;
    }
}

/**
 * Example 9: Copy text from the extension to the clipboard
 * Sends text from the extension to be added to clipboard history
 */
async function copyTextFromExtension(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/extension/copy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });
        const data = await response.json();
        
        if (data.success) {
            console.log('Text copied from extension, item ID:', data.item_id);
            return data.item_id;
        } else {
            console.error('Failed to copy text from extension:', data.error);
            return null;
        }
    } catch (error) {
        console.error('Error copying text from extension:', error);
        return null;
    }
}

// Usage examples

// In a browser extension, you could call these functions from background.js,
// content.js, or popup.js as needed:

/*
// When the extension starts
checkServerStatus().then(isRunning => {
    if (isRunning) {
        console.log('Connected to Clipboard Manager');
        getSystemInfo();
    } else {
        console.error('Cannot connect to Clipboard Manager');
    }
});

// When user clicks to add text
document.getElementById('addTextBtn').addEventListener('click', () => {
    const text = document.getElementById('textInput').value;
    addTextToClipboard(text);
});

// When searching for items
document.getElementById('searchBtn').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value;
    searchClipboard(query).then(items => {
        // Display items in UI
        displayItems(items);
    });
});

// Example function to display items (implementation would depend on your UI)
function displayItems(items) {
    const container = document.getElementById('itemsContainer');
    container.innerHTML = '';
    
    items.forEach(item => {
        const element = document.createElement('div');
        element.className = 'clipboard-item';
        element.textContent = item.preview;
        element.addEventListener('click', () => {
            // Handle item click
        });
        container.appendChild(element);
    });
}
*/

// Export functions for use in other files
export {
    getRecentItems,
    addTextToClipboard,
    toggleFavorite,
    searchClipboard,
    addTagToItem,
    deleteItem,
    checkServerStatus,
    getSystemInfo,
    copyTextFromExtension
};
