// ===========================
// Configuration
// ===========================

const API_URL = 'https://mxao4ksch0.execute-api.us-east-1.amazonaws.com/dev';

// ===========================
// DOM Elements
// ===========================

const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const clearSearchBtn = document.getElementById('clearSearchBtn');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const customLabelsInput = document.getElementById('customLabelsInput');
const uploadStatus = document.getElementById('uploadStatus');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const modalCaption = document.getElementById('modalCaption');
const loadingOverlay = document.getElementById('loadingOverlay');

// ===========================
// Event Listeners
// ===========================

// Search on Enter key
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchPhotos();
    }
});

// Show/hide clear button
searchInput.addEventListener('input', (e) => {
    clearSearchBtn.style.display = e.target.value ? 'block' : 'none';
});

// Clear search input
clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    clearSearchBtn.style.display = 'none';
    showWelcomeMessage();
});

// File input change - show preview and filename
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        // Update filename display
        fileName.textContent = file.name;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        fileName.textContent = 'Choose an image file';
        imagePreview.style.display = 'none';
    }
});

// Close modal on outside click
imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && imageModal.classList.contains('show')) {
        closeModal();
    }
});

// ===========================
// Search Functionality
// ===========================

async function searchPhotos() {
    const query = searchInput.value.trim();
    
    if (!query) {
        showStatus(searchResults, 'Please enter a search term.', 'error');
        return;
    }

    // Show loading state
    showLoadingState();

    try {
        const response = await fetch(
            `${API_URL}/search?q=${encodeURIComponent(query)}`,
            {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const imageUrls = await response.json();
        displayResults(imageUrls, query);

    } catch (error) {
        console.error('Error searching photos:', error);
        showErrorState('An error occurred while searching. Please try again.');
    }
}

// ===========================
// Display Functions
// ===========================

function showWelcomeMessage() {
    searchResults.innerHTML = `
        <div class="welcome-message">
            <i class="fas fa-images"></i>
            <h3>Start Searching</h3>
            <p>Enter keywords to find your photos using AI-powered search</p>
        </div>
    `;
}

function showLoadingState() {
    searchResults.innerHTML = `
        <div class="loading-state">
            <div class="spinner-small"></div>
            <p>Searching your photos...</p>
        </div>
    `;
}

function showErrorState(message) {
    searchResults.innerHTML = `
        <div class="no-results">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Oops!</h3>
            <p>${message}</p>
        </div>
    `;
}

function displayResults(imageUrls, query) {
    searchResults.innerHTML = '';

    if (!imageUrls || imageUrls.length === 0) {
        searchResults.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No photos found</h3>
                <p>We couldn't find any photos matching "${query}"</p>
                <p style="font-size: 0.9rem; margin-top: 1rem;">Try different keywords or upload more photos!</p>
            </div>
        `;
        return;
    }

    // Create results grid
    const grid = document.createElement('div');
    grid.className = 'results-grid';

    imageUrls.forEach((url, index) => {
        const card = createPhotoCard(url, index);
        grid.appendChild(card);
    });

    // Add results info
    const resultsInfo = document.createElement('div');
    resultsInfo.style.cssText = 'text-align: center; margin-bottom: 1.5rem; color: var(--text-secondary);';
    resultsInfo.innerHTML = `
        <i class="fas fa-check-circle" style="color: var(--secondary-color);"></i>
        Found <strong>${imageUrls.length}</strong> photo${imageUrls.length !== 1 ? 's' : ''} matching "<strong>${query}</strong>"
    `;

    searchResults.appendChild(resultsInfo);
    searchResults.appendChild(grid);

    // Animate results
    setTimeout(() => {
        grid.classList.add('animate-slide-up');
    }, 10);
}

function createPhotoCard(url, index) {
    const card = document.createElement('div');
    card.className = 'photo-card';
    card.onclick = () => openModal(url, index + 1);

    const img = document.createElement('img');
    img.src = url;
    img.alt = `Search result ${index + 1}`;
    img.loading = 'lazy';
    
    // Error handling for images
    img.onerror = () => {
        img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect width="400" height="300" fill="%23f0f0f0"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="16" fill="%23999"%3EImage not available%3C/text%3E%3C/svg%3E';
    };

    const overlay = document.createElement('div');
    overlay.className = 'photo-overlay';
    overlay.innerHTML = '<i class="fas fa-search-plus"></i>';

    card.appendChild(img);
    card.appendChild(overlay);

    return card;
}

// ===========================
// Upload Functionality
// ===========================

async function uploadPhoto() {
    const file = fileInput.files[0];
    const customLabels = customLabelsInput.value.trim();

    // Validation
    if (!file) {
        showUploadStatus('Please select a file to upload.', 'error');
        return;
    }

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showUploadStatus('Please upload a valid image file (JPEG, PNG, or WebP).', 'error');
        return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showUploadStatus('File size must be less than 10MB.', 'error');
        return;
    }

    const fileName = file.name;
    const contentType = file.type;

    // Show loading overlay
    showLoadingOverlay(true);
    showUploadStatus('Uploading your photo...', 'info');

    try {
        const headers = {
            'Content-Type': contentType
        };

        // Add custom labels if provided
        if (customLabels) {
            headers['x-amz-meta-customLabels'] = customLabels;
        }

        const response = await fetch(
            `${API_URL}/photos?filename=${encodeURIComponent(fileName)}`,
            {
                method: 'PUT',
                headers: headers,
                body: file
            }
        );

        if (response.ok) {
            showUploadStatus(
                '✓ Upload successful! Your photo will be indexed shortly.',
                'success'
            );
            
            // Reset form
            setTimeout(() => {
                resetUploadForm();
            }, 2000);
        } else {
            const errorText = await response.text();
            throw new Error(`Upload failed: ${response.status} - ${errorText}`);
        }
    } catch (error) {
        console.error('Error uploading photo:', error);
        showUploadStatus(
            'Upload failed. Please try again.',
            'error'
        );
    } finally {
        showLoadingOverlay(false);
    }
}

function resetUploadForm() {
    fileInput.value = '';
    customLabelsInput.value = '';
    fileName.textContent = 'Choose an image file';
    imagePreview.style.display = 'none';
    uploadStatus.classList.remove('show');
}

function showUploadStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `upload-status ${type} show`;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            uploadStatus.classList.remove('show');
        }, 5000);
    }
}

// ===========================
// Modal/Lightbox Functions
// ===========================

function openModal(url, photoNumber) {
    modalImage.src = url;
    modalCaption.textContent = `Photo ${photoNumber}`;
    imageModal.classList.add('show');
    document.body.style.overflow = 'hidden'; // Prevent background scroll
}

function closeModal() {
    imageModal.classList.remove('show');
    document.body.style.overflow = ''; // Restore scroll
}

// ===========================
// Utility Functions
// ===========================

function showLoadingOverlay(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showStatus(container, message, type) {
    const statusDiv = document.createElement('div');
    statusDiv.className = `upload-status ${type} show`;
    statusDiv.textContent = message;
    container.innerHTML = '';
    container.appendChild(statusDiv);
}

// ===========================
// Initialize
// ===========================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Photo Search App initialized');
    console.log('API URL:', API_URL);
});

// ===========================
// Service Worker
// ===========================

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed'));
    });
}
// dummy commit