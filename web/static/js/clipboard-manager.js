// Advanced Clipboard Manager - Web Interface

document.addEventListener('DOMContentLoaded', function() {
    // State variables
    let currentPage = 1;
    let currentFilter = 'all';
    let currentSearch = '';
    let selectedItemId = null;
    let allTags = [];
    
    // DOM elements
    const itemsList = document.getElementById('itemsList');
    const previewContent = document.getElementById('previewContent');
    const itemMetadata = document.getElementById('itemMetadata');
    const itemActions = document.getElementById('itemActions');
    const copyBtn = document.getElementById('copyBtn');
    const favoriteBtn = document.getElementById('favoriteBtn');
    const tagsBtn = document.getElementById('tagsBtn');
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const filterSelect = document.getElementById('filterSelect');
    const pagination = document.getElementById('pagination');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    
    // Tag modal elements
    const tagsModal = new bootstrap.Modal(document.getElementById('tagsModal'));
    const currentTagsList = document.getElementById('currentTagsList');
    const newTagInput = document.getElementById('newTagInput');
    const categoryTagCheck = document.getElementById('categoryTagCheck');
    const addTagBtn = document.getElementById('addTagBtn');
    const suggestedTags = document.getElementById('suggestedTags');
    
    // Initialize
    loadItems();
    loadAllTags();
    
    // Event listeners
    searchBtn.addEventListener('click', function() {
        currentSearch = searchInput.value;
        currentPage = 1;
        loadItems();
    });
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            currentSearch = searchInput.value;
            currentPage = 1;
            loadItems();
        }
    });
    
    filterSelect.addEventListener('change', function() {
        currentFilter = this.value.toLowerCase();
        if (currentFilter === 'all items') currentFilter = 'all';
        if (currentFilter === 'text only') currentFilter = 'text';
        if (currentFilter === 'images only') currentFilter = 'image';
        currentPage = 1;
        loadItems();
    });
    
    copyBtn.addEventListener('click', function() {
        if (!selectedItemId) return;
        
        fetchItemContent(selectedItemId)
            .then(content => {
                if (content.type === 'text') {
                    copyTextToClipboard(content.content);
                    showToast('Text copied to clipboard');
                } else {
                    // For images, we need to handle differently
                    // We'll download the image and then use the Clipboard API
                    const img = new Image();
                    img.onload = function() {
                        const canvas = document.createElement('canvas');
                        canvas.width = img.width;
                        canvas.height = img.height;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0);
                        canvas.toBlob(function(blob) {
                            navigator.clipboard.write([
                                new ClipboardItem({ 'image/png': blob })
                            ]).then(function() {
                                showToast('Image copied to clipboard');
                            }).catch(function(err) {
                                console.error('Could not copy image: ', err);
                                showToast('Failed to copy image', 'error');
                            });
                        });
                    };
                    img.src = content.image_data;
                }
            })
            .catch(error => {
                console.error('Error copying to clipboard:', error);
                showToast('Failed to copy to clipboard', 'error');
            });
    });
    
    favoriteBtn.addEventListener('click', function() {
        if (!selectedItemId) return;
        
        fetch(`/api/item/${selectedItemId}/favorite`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const isFavorite = data.favorite;
                favoriteBtn.innerHTML = isFavorite ? 
                    '<i class="fas fa-star"></i>' : 
                    '<i class="far fa-star"></i>';
                
                // Update the item in the list
                const itemElement = document.querySelector(`[data-item-id="${selectedItemId}"]`);
                if (itemElement) {
                    const favoriteIcon = itemElement.querySelector('.clipboard-item-favorite');
                    if (favoriteIcon) {
                        favoriteIcon.innerHTML = isFavorite ? 
                            '<i class="fas fa-star"></i>' : 
                            '<i class="far fa-star"></i>';
                    }
                }
                
                showToast(isFavorite ? 'Added to favorites' : 'Removed from favorites');
                
                // Reload if we're in favorites filter
                if (currentFilter === 'favorites') {
                    loadItems();
                }
            } else {
                showToast('Failed to update favorite status', 'error');
            }
        })
        .catch(error => {
            console.error('Error toggling favorite:', error);
            showToast('Failed to update favorite status', 'error');
        });
    });
    
    tagsBtn.addEventListener('click', function() {
        if (!selectedItemId) return;
        
        // Clear previous tags
        currentTagsList.innerHTML = '';
        newTagInput.value = '';
        categoryTagCheck.checked = false;
        
        // Load tags for this item
        fetch(`/api/item/${selectedItemId}/tags`)
            .then(response => response.json())
            .then(data => {
                if (data.tags && data.tags.length > 0) {
                    // Display current tags
                    data.tags.forEach(tag => {
                        addTagToUI(tag, currentTagsList, true);
                    });
                } else {
                    currentTagsList.innerHTML = '<span class="text-muted">No tags</span>';
                }
                
                // Update suggested tags
                updateSuggestedTags(data.tags || []);
                
                // Show the modal
                tagsModal.show();
            })
            .catch(error => {
                console.error('Error loading tags:', error);
                showToast('Failed to load tags', 'error');
            });
    });
    
    addTagBtn.addEventListener('click', function() {
        addTagToItem();
    });
    
    newTagInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addTagToItem();
        }
    });
    
    clearHistoryBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear your clipboard history? Favorites will be kept.')) {
            fetch('/api/items/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ keep_favorites: true })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(`Cleared ${data.deleted_count} items from history`);
                    // Reset view
                    selectedItemId = null;
                    loadItems();
                    resetPreview();
                } else {
                    showToast('Failed to clear history', 'error');
                }
            })
            .catch(error => {
                console.error('Error clearing history:', error);
                showToast('Failed to clear history', 'error');
            });
        }
    });
    
    // Functions
    function loadItems() {
        itemsList.innerHTML = `
            <div class="text-center py-4 text-muted">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading clipboard items...</p>
            </div>
        `;
        
        fetch(`/api/items?filter=${currentFilter}&search=${encodeURIComponent(currentSearch)}&page=${currentPage}`)
            .then(response => response.json())
            .then(data => {
                if (data.items.length === 0) {
                    itemsList.innerHTML = `
                        <div class="no-items">
                            <i class="fas fa-clipboard fa-2x mb-3 opacity-25"></i>
                            <p>No clipboard items found</p>
                            ${currentSearch ? `<p class="small">Try a different search term</p>` : ''}
                        </div>
                    `;
                    pagination.innerHTML = '';
                    return;
                }
                
                // Render items
                itemsList.innerHTML = '';
                data.items.forEach(item => {
                    const itemElement = document.createElement('a');
                    itemElement.href = '#';
                    itemElement.className = 'list-group-item list-group-item-action clipboard-item d-flex justify-content-between align-items-start';
                    itemElement.setAttribute('data-item-id', item.id);
                    
                    // Format the content preview
                    let contentPreview = '';
                    if (item.type === 'text') {
                        contentPreview = `<span class="text-truncate">${escapeHtml(item.preview)}</span>`;
                    } else {
                        contentPreview = '<span><i class="fas fa-image me-1"></i> [Image]</span>';
                    }
                    
                    // Format the favorite icon
                    const favoriteIcon = item.favorite ? 
                        '<i class="fas fa-star"></i>' : 
                        '<i class="far fa-star"></i>';
                    
                    itemElement.innerHTML = `
                        <div class="ms-2 me-auto">
                            <div class="d-flex align-items-center">
                                <span class="badge bg-${item.type === 'text' ? 'primary' : 'success'} me-2">
                                    ${item.type === 'text' ? 'Text' : 'Image'}
                                </span>
                                ${contentPreview}
                            </div>
                            <div class="small text-muted mt-1">
                                <i class="far fa-clock me-1"></i>${item.timestamp}
                            </div>
                        </div>
                        <span class="clipboard-item-favorite">${favoriteIcon}</span>
                    `;
                    
                    itemElement.addEventListener('click', function(e) {
                        e.preventDefault();
                        selectItem(item.id);
                    });
                    
                    itemsList.appendChild(itemElement);
                });
                
                // Create pagination
                updatePagination(data.page, data.total_pages);
                
                // Select the first item if none is selected
                if (!selectedItemId && data.items.length > 0) {
                    selectItem(data.items[0].id);
                }
            })
            .catch(error => {
                console.error('Error loading items:', error);
                itemsList.innerHTML = `
                    <div class="alert alert-danger m-3">
                        Failed to load clipboard items: ${error.message}
                    </div>
                `;
            });
    }
    
    function selectItem(itemId) {
        selectedItemId = itemId;
        
        // Update selection in the UI
        document.querySelectorAll('.clipboard-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const selectedElement = document.querySelector(`[data-item-id="${itemId}"]`);
        if (selectedElement) {
            selectedElement.classList.add('active');
        }
        
        // Show loading state in preview
        previewContent.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading item preview...</p>
            </div>
        `;
        
        itemMetadata.innerHTML = '';
        
        // Show action buttons
        itemActions.classList.remove('d-none');
        
        // Fetch item data
        fetch(`/api/item/${itemId}`)
            .then(response => response.json())
            .then(item => {
                // Update favorite button
                favoriteBtn.innerHTML = item.favorite ? 
                    '<i class="fas fa-star"></i>' : 
                    '<i class="far fa-star"></i>';
                
                // Display the content based on type
                if (item.type === 'text') {
                    previewContent.innerHTML = `
                        <div class="text-preview">${escapeHtml(item.content)}</div>
                    `;
                } else {
                    previewContent.innerHTML = `
                        <img src="${item.image_data}" alt="Clipboard Image" class="image-preview">
                    `;
                }
                
                // Display metadata
                itemMetadata.innerHTML = `
                    <div class="metadata-item">
                        <i class="far fa-clock"></i> ${item.timestamp}
                    </div>
                    <div class="metadata-item">
                        <i class="far fa-file"></i> ${item.type === 'text' ? 'Text' : 'Image'}
                    </div>
                `;
                
                // Display tags if any
                if (item.tags && item.tags.length > 0) {
                    const tagsHtml = item.tags.map(tag => {
                        const isCategory = tag.startsWith('#') || tag.startsWith('@');
                        return `<span class="tag ${isCategory ? 'category-tag' : ''}">${escapeHtml(tag)}</span>`;
                    }).join('');
                    
                    itemMetadata.innerHTML += `
                        <div class="mt-2">
                            ${tagsHtml}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading item:', error);
                previewContent.innerHTML = `
                    <div class="alert alert-danger m-3">
                        Failed to load item preview: ${error.message}
                    </div>
                `;
            });
    }
    
    function resetPreview() {
        previewContent.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="fas fa-clipboard fa-4x mb-3 opacity-25"></i>
                <p>Select an item to preview its content</p>
            </div>
        `;
        itemMetadata.innerHTML = '';
        itemActions.classList.add('d-none');
    }
    
    function updatePagination(currentPage, totalPages) {
        pagination.innerHTML = '';
        
        if (totalPages <= 1) {
            return;
        }
        
        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>`;
        prevLi.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        });
        pagination.appendChild(prevLi);
        
        // Page numbers
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            pageLi.addEventListener('click', function(e) {
                e.preventDefault();
                goToPage(i);
            });
            pagination.appendChild(pageLi);
        }
        
        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>`;
        nextLi.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                goToPage(currentPage + 1);
            }
        });
        pagination.appendChild(nextLi);
    }
    
    function goToPage(page) {
        currentPage = page;
        loadItems();
        // Scroll to top of items list
        itemsList.scrollTop = 0;
    }
    
    function loadAllTags() {
        fetch('/api/tags')
            .then(response => response.json())
            .then(data => {
                allTags = data.tags;
            })
            .catch(error => {
                console.error('Error loading tags:', error);
            });
    }
    
    function updateSuggestedTags(currentItemTags) {
        suggestedTags.innerHTML = '';
        
        if (allTags.length === 0) {
            suggestedTags.innerHTML = '<span class="text-muted">No tags available</span>';
            return;
        }
        
        // Filter out tags that are already applied to this item
        const filteredTags = allTags.filter(tag => !currentItemTags.includes(tag));
        
        if (filteredTags.length === 0) {
            suggestedTags.innerHTML = '<span class="text-muted">No additional tags available</span>';
            return;
        }
        
        // Add suggested tags
        filteredTags.forEach(tag => {
            addTagToUI(tag, suggestedTags, false, true);
        });
    }
    
    function addTagToUI(tag, container, removable = false, clickable = false) {
        const isCategory = tag.startsWith('#') || tag.startsWith('@');
        const tagElement = document.createElement('span');
        tagElement.className = `tag ${isCategory ? 'category-tag' : ''}`;
        
        if (removable) {
            tagElement.innerHTML = `
                ${escapeHtml(tag)}
                <i class="fas fa-times" data-tag="${escapeHtml(tag)}"></i>
            `;
            
            // Add event listener to remove button
            tagElement.querySelector('.fa-times').addEventListener('click', function() {
                removeTagFromItem(this.getAttribute('data-tag'));
            });
        } else {
            tagElement.textContent = tag;
            
            if (clickable) {
                tagElement.style.cursor = 'pointer';
                tagElement.addEventListener('click', function() {
                    newTagInput.value = tag;
                    addTagToItem();
                });
            }
        }
        
        container.appendChild(tagElement);
    }
    
    function addTagToItem() {
        if (!selectedItemId) return;
        
        const tag = newTagInput.value.trim();
        if (!tag) return;
        
        let finalTag = tag;
        
        // Add category prefix if checkbox is checked
        if (categoryTagCheck.checked && !tag.startsWith('#') && !tag.startsWith('@')) {
            finalTag = '#' + tag;
        }
        
        fetch(`/api/item/${selectedItemId}/tags`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tag: finalTag })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear input
                newTagInput.value = '';
                categoryTagCheck.checked = false;
                
                // Update the tags display
                currentTagsList.innerHTML = '';
                data.tags.forEach(tag => {
                    addTagToUI(tag, currentTagsList, true);
                });
                
                // Update suggested tags
                updateSuggestedTags(data.tags);
                
                // Refresh all tags list
                loadAllTags();
                
                // Show success message
                showToast(`Tag "${finalTag}" added`);
            } else {
                showToast('Failed to add tag', 'error');
            }
        })
        .catch(error => {
            console.error('Error adding tag:', error);
            showToast('Failed to add tag', 'error');
        });
    }
    
    function removeTagFromItem(tag) {
        if (!selectedItemId) return;
        
        fetch(`/api/item/${selectedItemId}/tags/${encodeURIComponent(tag)}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the tags display
                currentTagsList.innerHTML = '';
                if (data.tags.length > 0) {
                    data.tags.forEach(tag => {
                        addTagToUI(tag, currentTagsList, true);
                    });
                } else {
                    currentTagsList.innerHTML = '<span class="text-muted">No tags</span>';
                }
                
                // Update suggested tags
                updateSuggestedTags(data.tags);
                
                showToast(`Tag "${tag}" removed`);
            } else {
                showToast('Failed to remove tag', 'error');
            }
        })
        .catch(error => {
            console.error('Error removing tag:', error);
            showToast('Failed to remove tag', 'error');
        });
    }
    
    // Helper functions
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function copyTextToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text)
                .catch(err => {
                    console.error('Could not copy text: ', err);
                });
        } else {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            
            try {
                document.execCommand('copy');
            } catch (err) {
                console.error('Failed to copy: ', err);
            }
            
            document.body.removeChild(textarea);
        }
    }
    
    function fetchItemContent(itemId) {
        return fetch(`/api/item/${itemId}`)
            .then(response => response.json());
    }
    
    function showToast(message, type = 'success') {
        // Create a toast element
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
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
});