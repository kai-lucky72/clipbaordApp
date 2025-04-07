// Advanced Clipboard Manager - Content Script

// This script runs in the context of web pages to help with clipboard operations

// Global state
let quickPastePopup = null;
let isPopupVisible = false;

// Create and inject styles for the popup
const injectStyles = () => {
  const styleEl = document.createElement('style');
  styleEl.textContent = `
    .clipboard-manager-popup {
      position: absolute;
      width: 280px;
      max-height: 300px;
      background-color: white;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      z-index: 2147483647;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      opacity: 0;
      transform: translateY(10px);
      transition: opacity 0.15s ease-out, transform 0.15s ease-out;
    }
    
    .clipboard-manager-popup.visible {
      opacity: 1;
      transform: translateY(0);
    }
    
    .clipboard-items {
      max-height: 250px;
      overflow-y: auto;
    }
    
    .clipboard-item {
      padding: 10px 12px;
      border-bottom: 1px solid #f0f0f0;
      cursor: pointer;
      font-size: 13px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: #333;
    }
    
    .clipboard-item:hover {
      background-color: #f5f8ff;
    }
    
    .clipboard-item.text-item:before {
      content: "📄 ";
      opacity: 0.5;
    }
    
    .clipboard-item.image-item:before {
      content: "🖼️ ";
      opacity: 0.5;
    }
    
    .clipboard-footer {
      padding: 8px 12px;
      font-size: 12px;
      text-align: center;
      background-color: #f7f7f7;
      border-top: 1px solid #eaeaea;
    }
    
    .clipboard-footer a {
      color: #4a6cf7;
      text-decoration: none;
    }
    
    .clipboard-footer a:hover {
      text-decoration: underline;
    }
  `;
  document.head.appendChild(styleEl);
};

// Create quick paste popup
const createQuickPastePopup = () => {
  // If a popup already exists, remove it
  if (quickPastePopup) {
    document.body.removeChild(quickPastePopup);
  }
  
  // Create a new popup
  quickPastePopup = document.createElement('div');
  quickPastePopup.className = 'clipboard-manager-popup';
  quickPastePopup.innerHTML = `
    <div class="clipboard-items"></div>
    <div class="clipboard-footer">
      <a href="http://localhost:5000" target="_blank">Open Clipboard Manager</a>
    </div>
  `;
  
  // Add it to the page but keep it hidden
  document.body.appendChild(quickPastePopup);
  
  // Close the popup when clicking outside
  document.addEventListener('click', (e) => {
    if (isPopupVisible && !quickPastePopup.contains(e.target)) {
      hideQuickPastePopup();
    }
  });
  
  // Close on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isPopupVisible) {
      hideQuickPastePopup();
    }
  });
  
  return quickPastePopup;
};

// Show quick paste popup near the cursor position
const showQuickPastePopup = async (x, y) => {
  if (!quickPastePopup) {
    injectStyles();
    createQuickPastePopup();
  }
  
  // Position the popup near the cursor
  quickPastePopup.style.left = `${x}px`;
  quickPastePopup.style.top = `${y}px`;
  
  // Get the 5 most recent clipboard items
  try {
    const response = await fetch('http://localhost:5000/api/items?per_page=5');
    const data = await response.json();
    
    const itemsContainer = quickPastePopup.querySelector('.clipboard-items');
    itemsContainer.innerHTML = '';
    
    if (data.items && data.items.length > 0) {
      data.items.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = `clipboard-item ${item.type}-item`;
        
        if (item.type === 'text') {
          // Limit text to a reasonable length
          const previewText = item.preview || '';
          itemElement.textContent = previewText;
        } else if (item.type === 'image') {
          itemElement.textContent = 'Image';
        }
        
        // When an item is clicked, paste it and hide the popup
        itemElement.addEventListener('click', async () => {
          // Get full item content
          const itemResponse = await fetch(`http://localhost:5000/api/item/${item.id}`);
          const itemData = await itemResponse.json();
          
          if (itemData.type === 'text') {
            // Find active element
            const activeElement = document.activeElement;
            
            if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.isContentEditable)) {
              // Get current selection
              const start = activeElement.selectionStart || 0;
              const end = activeElement.selectionEnd || 0;
              
              // Get text to paste
              const textToPaste = itemData.content || '';
              
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
            }
          } else if (itemData.type === 'image' && itemData.image_data) {
            // For images, we can use clipboard API to copy the image
            try {
              // Create an image element to load the image
              const img = new Image();
              img.src = itemData.image_data;
              img.onload = () => {
                // Create a canvas to draw the image
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                
                // Convert canvas to blob
                canvas.toBlob(blob => {
                  // Try using Clipboard API to write the image
                  navigator.clipboard.write([
                    new ClipboardItem({ 'image/png': blob })
                  ]).catch(err => {
                    console.error('Could not copy image:', err);
                  });
                });
              };
            } catch (error) {
              console.error('Error copying image:', error);
            }
          }
          
          // Hide popup after pasting
          hideQuickPastePopup();
        });
        
        itemsContainer.appendChild(itemElement);
      });
    } else {
      // No items
      const noItemsElement = document.createElement('div');
      noItemsElement.className = 'clipboard-item';
      noItemsElement.textContent = 'No clipboard items found';
      itemsContainer.appendChild(noItemsElement);
    }
    
    // Show the popup
    isPopupVisible = true;
    quickPastePopup.classList.add('visible');
    
  } catch (error) {
    console.error('Error fetching clipboard items:', error);
    // Show error in popup
    const itemsContainer = quickPastePopup.querySelector('.clipboard-items');
    itemsContainer.innerHTML = `
      <div class="clipboard-item">
        Error connecting to Clipboard Manager server.
        Make sure it's running at http://localhost:5000
      </div>
    `;
    
    // Show the popup
    isPopupVisible = true;
    quickPastePopup.classList.add('visible');
  }
};

// Hide quick paste popup
const hideQuickPastePopup = () => {
  if (quickPastePopup) {
    quickPastePopup.classList.remove('visible');
    isPopupVisible = false;
  }
};

// Listen for copy event to track copied content
document.addEventListener('copy', (event) => {
  setTimeout(() => {
    // Read from clipboard
    navigator.clipboard.readText().then(text => {
      if (text) {
        // Send to background script for storage
        chrome.runtime.sendMessage({
          action: 'copyToClipboard',
          text: text
        });
      }
    }).catch(err => {
      console.error('Could not read clipboard contents:', err);
    });
  }, 100); // Small delay to ensure clipboard has been updated
});

// Listen for paste event to show quick paste popup
document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'v') {
    // Show quick paste popup near cursor position
    showQuickPastePopup(event.clientX || window.innerWidth / 2, event.clientY + 20 || window.innerHeight / 2);
    
    // Don't prevent default paste operation - user can still use normal paste
    // This just shows our options alongside it
  }
});

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
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
  
  // Handle get selected text request
  if (request.action === 'getSelectedText') {
    const selection = window.getSelection().toString().trim();
    sendResponse({ text: selection });
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
