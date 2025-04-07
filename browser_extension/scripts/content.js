// Advanced Clipboard Manager - Content Script

// This script runs in the context of web pages to help with clipboard operations

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Handle copy request that needs page context
  if (request.action === 'getSelectedText') {
    const selection = window.getSelection().toString().trim();
    sendResponse({ text: selection });
  }
  
  // Handle paste request
  if (request.action === 'pasteText') {
    // Find active element
    const activeElement = document.activeElement;
    
    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.isContentEditable)) {
      // Get current selection
      const start = activeElement.selectionStart || 0;
      const end = activeElement.selectionEnd || 0;
      
      // Get text to paste
      const textToPaste = request.text || '';
      
      if (activeElement.isContentEditable) {
        // Handle contentEditable elements
        document.execCommand('insertText', false, textToPaste);
      } else {
        // Handle regular input elements
        const currentValue = activeElement.value || '';
        const beforeText = currentValue.substring(0, start);
        const afterText = currentValue.substring(end);
        
        // Set new value
        activeElement.value = beforeText + textToPaste + afterText;
        
        // Position cursor after pasted text
        activeElement.selectionStart = activeElement.selectionEnd = start + textToPaste.length;
        
        // Dispatch input event to trigger any listeners
        const event = new Event('input', { bubbles: true });
        activeElement.dispatchEvent(event);
      }
      
      sendResponse({ success: true });
    } else {
      sendResponse({ success: false, error: 'No valid input element focused' });
    }
  }
  
  // Return true to indicate asynchronous response
  return true;
});

// Detect when something is copied on the page
document.addEventListener('copy', (event) => {
  // Get selected text
  const selection = window.getSelection().toString().trim();
  
  if (selection) {
    // Send to background script
    chrome.runtime.sendMessage({
      action: 'textCopied',
      text: selection
    });
  }
});

// Add right-click context menu for easier copying
document.addEventListener('mousedown', (event) => {
  // Right click
  if (event.button === 2) {
    // Get selected text
    const selection = window.getSelection().toString().trim();
    
    // Save selection to storage for context menu
    if (selection) {
      chrome.storage.local.set({ currentSelection: selection });
    }
  }
});
