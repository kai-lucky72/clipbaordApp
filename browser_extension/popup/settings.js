// Advanced Clipboard Manager - Settings Script

// DOM elements
const monitorClipboardCheckbox = document.getElementById('monitorClipboard');
const showNotificationsCheckbox = document.getElementById('showNotifications');
const autoConnectCheckbox = document.getElementById('autoConnect');
const serverUrlInput = document.getElementById('serverUrl');
const testConnectionBtn = document.getElementById('testConnectionBtn');
const connectionStatus = document.getElementById('connectionStatus');
const resetBtn = document.getElementById('resetBtn');
const saveBtn = document.getElementById('saveBtn');
const backBtn = document.getElementById('backBtn');

// Default settings
const defaultSettings = {
    monitorClipboard: true,
    showNotifications: true,
    autoConnect: true,
    serverUrl: 'http://localhost:5000/api'
};

// Load settings when page loads
document.addEventListener('DOMContentLoaded', loadSettings);

// Set up event listeners
testConnectionBtn.addEventListener('click', testConnection);
resetBtn.addEventListener('click', resetSettings);
saveBtn.addEventListener('click', saveSettings);
backBtn.addEventListener('click', function() {
    window.location.href = 'popup.html';
});

// Load settings from storage
function loadSettings() {
    chrome.runtime.sendMessage({ action: 'getSettings' }, function(response) {
        const settings = response.settings || defaultSettings;
        
        // Update UI
        monitorClipboardCheckbox.checked = settings.monitorClipboard;
        showNotificationsCheckbox.checked = settings.showNotifications;
        autoConnectCheckbox.checked = settings.autoConnect;
        serverUrlInput.value = settings.serverUrl || defaultSettings.serverUrl;
    });
}

// Test connection to server
function testConnection() {
    const serverUrl = serverUrlInput.value.trim();
    if (!serverUrl) {
        showConnectionStatus('error', 'Server URL cannot be empty');
        return;
    }
    
    // Update UI
    testConnectionBtn.disabled = true;
    testConnectionBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Testing...';
    showConnectionStatus('info', 'Testing connection...');
    
    // Extract base URL without /api if present
    const baseUrl = serverUrl.endsWith('/api') ? 
        serverUrl.substring(0, serverUrl.length - 4) : 
        serverUrl;
    
    // Make test request
    fetch(`${baseUrl}/api/ping`)
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        })
        .then(data => {
            if (data.success) {
                showConnectionStatus('success', 'Connection successful! Server is running.');
            } else {
                showConnectionStatus('warning', 'Server responded but returned an unexpected response.');
            }
        })
        .catch(error => {
            console.error('Connection test failed:', error);
            showConnectionStatus('error', `Connection failed: ${error.message}`);
        })
        .finally(() => {
            // Reset button
            testConnectionBtn.disabled = false;
            testConnectionBtn.innerHTML = 'Test';
        });
}

// Show connection status with appropriate styling
function showConnectionStatus(type, message) {
    connectionStatus.className = 'alert';
    let icon = '';
    
    switch (type) {
        case 'success':
            connectionStatus.classList.add('alert-success');
            icon = 'fas fa-check-circle';
            break;
        case 'error':
            connectionStatus.classList.add('alert-danger');
            icon = 'fas fa-exclamation-circle';
            break;
        case 'warning':
            connectionStatus.classList.add('alert-warning');
            icon = 'fas fa-exclamation-triangle';
            break;
        default:
            connectionStatus.classList.add('alert-info');
            icon = 'fas fa-info-circle';
    }
    
    connectionStatus.innerHTML = `<i class="${icon} me-2"></i>${message}`;
}

// Reset settings to defaults
function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
        // Update UI
        monitorClipboardCheckbox.checked = defaultSettings.monitorClipboard;
        showNotificationsCheckbox.checked = defaultSettings.showNotifications;
        autoConnectCheckbox.checked = defaultSettings.autoConnect;
        serverUrlInput.value = defaultSettings.serverUrl;
        
        // Save to storage
        chrome.runtime.sendMessage({ 
            action: 'saveSettings', 
            settings: defaultSettings 
        }, function(response) {
            if (response.success) {
                showToast('Settings reset to defaults', 'success');
            }
        });
    }
}

// Save settings
function saveSettings() {
    const settings = {
        monitorClipboard: monitorClipboardCheckbox.checked,
        showNotifications: showNotificationsCheckbox.checked,
        autoConnect: autoConnectCheckbox.checked,
        serverUrl: serverUrlInput.value.trim()
    };
    
    chrome.runtime.sendMessage({ 
        action: 'saveSettings', 
        settings: settings 
    }, function(response) {
        if (response.success) {
            showToast('Settings saved successfully', 'success');
        } else {
            showToast('Failed to save settings', 'error');
        }
    });
}

// Show toast notification
function showToast(message, type = 'success') {
    // Create a toast element
    const toastId = 'toast-' + Date.now();
    const icon = type === 'success' ? 
        '<i class="fas fa-check-circle text-success me-2"></i>' : 
        '<i class="fas fa-exclamation-circle text-danger me-2"></i>';
        
    const toastHtml = `
        <div id="${toastId}" class="toast toast-${type} fade show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                ${icon}
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Create container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Add the toast to the container
    toastContainer.innerHTML += toastHtml;
    
    // Initialize and show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 3000 });
    toast.show();
    
    // Remove the toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}
