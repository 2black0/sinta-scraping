// SINTA Scraper Web Interface JavaScript

// Global variables
let scrapingInterval = null;
let isScrapingRunning = false;

// DOM elements
const lecturerIdsTextarea = document.getElementById('lecturer-ids');
const lecturerCountSpan = document.getElementById('lecturer-count');
const saveLecturersBtn = document.getElementById('save-lecturers-btn');
const startScrapingBtn = document.getElementById('start-scraping-btn');
const progressSection = document.getElementById('progress-section');
const progressBar = document.getElementById('progress-bar');
const progressMessage = document.getElementById('progress-message');
const progressPercentage = document.getElementById('progress-percentage');
const elapsedTimeSpan = document.getElementById('elapsed-time');
const outputDirectorySpan = document.getElementById('output-directory');
const loadingModal = document.getElementById('loading-modal');
const statusIndicator = document.getElementById('status-indicator');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    updateLecturerCount();
    checkInitialStatus();
});

// Initialize event listeners
function initializeEventListeners() {
    // Lecturer IDs management
    lecturerIdsTextarea.addEventListener('input', updateLecturerCount);
    saveLecturersBtn.addEventListener('click', saveLecturerIds);
    
    // Scraping controls
    startScrapingBtn.addEventListener('click', startScraping);
    
    // Category selection
    const allCheckbox = document.getElementById('cat-all');
    const categoryCheckboxes = document.querySelectorAll('.category-checkbox:not(#cat-all)');
    
    allCheckbox.addEventListener('change', function() {
        categoryCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
    });
    
    categoryCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const checkedCategories = Array.from(categoryCheckboxes).filter(cb => cb.checked);
            allCheckbox.checked = checkedCategories.length === categoryCheckboxes.length;
        });
    });
    
    // Smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Update lecturer count
function updateLecturerCount() {
    const text = lecturerIdsTextarea.value;
    const lines = text.split('\n').filter(line => {
        const trimmed = line.trim();
        return trimmed && !trimmed.startsWith('#');
    });
    
    lecturerCountSpan.textContent = `${lines.length} dosen`;
}

// Save lecturer IDs to server
async function saveLecturerIds() {
    const text = lecturerIdsTextarea.value;
    const lecturerIds = text.split('\n').filter(line => {
        const trimmed = line.trim();
        return trimmed && !trimmed.startsWith('#');
    });
    
    try {
        showLoading(saveLecturersBtn, 'Menyimpan...');
        
        const response = await fetch('/api/lecturers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ lecturer_ids: lecturerIds })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Daftar dosen berhasil disimpan!', 'success');
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        hideLoading(saveLecturersBtn, 'Simpan');
    }
}

// Start scraping process
async function startScraping() {
    if (isScrapingRunning) {
        showToast('Scraping sudah berjalan!', 'warning');
        return;
    }
    
    // Get selected categories
    const categoryCheckboxes = document.querySelectorAll('.category-checkbox:not(#cat-all)');
    const selectedCategories = Array.from(categoryCheckboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);
    
    // Validate lecturer IDs
    const lecturerIds = lecturerIdsTextarea.value.split('\n').filter(line => {
        const trimmed = line.trim();
        return trimmed && !trimmed.startsWith('#');
    });
    
    if (lecturerIds.length === 0) {
        showToast('Silakan masukkan minimal satu ID dosen!', 'error');
        return;
    }
    
    try {
        // Show loading modal
        showModal(loadingModal);
        
        // Save lecturer IDs first
        await saveLecturerIds();
        
        // Start scraping
        const response = await fetch('/api/start-scraping', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ categories: selectedCategories })
        });
        
        const result = await response.json();
        
        if (result.success) {
            hideModal(loadingModal);
            showProgressSection();
            startProgressMonitoring();
            showToast('Scraping dimulai!', 'success');
        } else {
            hideModal(loadingModal);
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        hideModal(loadingModal);
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Show progress section
function showProgressSection() {
    progressSection.classList.remove('hidden');
    progressSection.scrollIntoView({ behavior: 'smooth' });
    
    // Update UI state
    isScrapingRunning = true;
    startScrapingBtn.disabled = true;
    startScrapingBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scraping...';
    startScrapingBtn.classList.add('opacity-50', 'cursor-not-allowed');
    
    // Show status indicator
    statusIndicator.classList.remove('hidden');
    statusIndicator.classList.add('flex');
    statusIndicator.querySelector('span').textContent = 'Running';
    statusIndicator.querySelector('.w-3').classList.remove('bg-green-500');
    statusIndicator.querySelector('.w-3').classList.add('bg-yellow-500');
}

// Hide progress section
function hideProgressSection() {
    // Update UI state
    isScrapingRunning = false;
    startScrapingBtn.disabled = false;
    startScrapingBtn.innerHTML = 'Start Scraping';
    startScrapingBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    
    // Update status indicator
    statusIndicator.querySelector('span').textContent = 'Ready';
    statusIndicator.querySelector('.w-3').classList.remove('bg-yellow-500');
    statusIndicator.querySelector('.w-3').classList.add('bg-green-500');
}

// Start progress monitoring
function startProgressMonitoring() {
    scrapingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/scraping-status');
            const status = await response.json();
            
            updateProgressUI(status);
            
            if (!status.running) {
                stopProgressMonitoring();
                handleScrapingComplete(status);
            }
        } catch (error) {
            console.error('Error checking scraping status:', error);
        }
    }, 2000); // Check every 2 seconds
}

// Stop progress monitoring
function stopProgressMonitoring() {
    if (scrapingInterval) {
        clearInterval(scrapingInterval);
        scrapingInterval = null;
    }
}

// Update progress UI
function updateProgressUI(status) {
    // Update progress bar
    progressBar.style.width = `${status.progress}%`;
    progressPercentage.textContent = `${status.progress}%`;
    
    // Update message
    progressMessage.textContent = status.message || 'Processing...';
    
    // Update elapsed time
    if (status.elapsed_time) {
        elapsedTimeSpan.textContent = `Waktu: ${status.elapsed_time}`;
    }
    
    // Update output directory
    if (status.output_dir) {
        outputDirectorySpan.textContent = `Output: ${status.output_dir}`;
    }
    
    // Add animation to progress bar if running
    if (status.running && status.progress < 100) {
        progressBar.classList.add('progress-bar-animated');
    } else {
        progressBar.classList.remove('progress-bar-animated');
    }
}

// Handle scraping completion
function handleScrapingComplete(status) {
    hideProgressSection();
    
    if (status.results && status.results.success) {
        showToast('Scraping selesai! Hasil tersedia di bagian Results.', 'success');
        // Refresh results section
        setTimeout(() => {
            location.reload(); // Simple refresh to update results
        }, 2000);
    } else {
        const errorMsg = status.results?.error || status.message || 'Terjadi kesalahan';
        showToast(`Scraping gagal: ${errorMsg}`, 'error');
    }
}

// Check initial status on page load
async function checkInitialStatus() {
    try {
        const response = await fetch('/api/scraping-status');
        const status = await response.json();
        
        if (status.running) {
            showProgressSection();
            startProgressMonitoring();
        } else {
            statusIndicator.classList.remove('hidden');
            statusIndicator.classList.add('flex');
        }
    } catch (error) {
        console.error('Error checking initial status:', error);
    }
}

// Utility functions
function showLoading(button, text) {
    button.disabled = true;
    button.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${text}`;
}

function hideLoading(button, text) {
    button.disabled = false;
    button.innerHTML = `<i class="fas fa-save mr-2"></i>${text}`;
}

function showModal(modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function hideModal(modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-circle' : 
                 'fa-info-circle';
    
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${icon} mr-3 text-lg"></i>
            <div>
                <div class="font-medium">${message}</div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Download all files from a specific output directory
function downloadAllFiles(outputDir) {
    // This would need to be implemented on the server side
    // For now, show a message
    showToast('Fitur download semua akan segera tersedia!', 'info');
}

// Refresh results
async function refreshResults() {
    try {
        const response = await fetch('/api/outputs');
        const data = await response.json();
        
        // Update results section
        // This is a simplified implementation
        // In a real app, you'd update the DOM with the new data
        showToast('Results refreshed!', 'success');
    } catch (error) {
        showToast('Error refreshing results', 'error');
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save lecturers
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveLecturerIds();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal, #loading-modal');
        modals.forEach(modal => {
            if (!modal.classList.contains('hidden')) {
                hideModal(modal);
            }
        });
    }
});

// Handle page visibility change
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, reduce polling frequency
        if (scrapingInterval) {
            stopProgressMonitoring();
            scrapingInterval = setInterval(async () => {
                try {
                    const response = await fetch('/api/scraping-status');
                    const status = await response.json();
                    
                    if (!status.running) {
                        stopProgressMonitoring();
                        handleScrapingComplete(status);
                    }
                } catch (error) {
                    console.error('Error checking scraping status:', error);
                }
            }, 10000); // Check every 10 seconds when hidden
        }
    } else {
        // Page is visible, resume normal polling
        if (isScrapingRunning) {
            stopProgressMonitoring();
            startProgressMonitoring();
        }
    }
});

// Export functions for global access
window.downloadAllFiles = downloadAllFiles;
window.scrollToSection = scrollToSection;
window.refreshResults = refreshResults;
