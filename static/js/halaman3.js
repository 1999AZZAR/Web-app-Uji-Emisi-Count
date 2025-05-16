// halaman3.js - JavaScript functionality for halaman3.html

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers and filters
    initializeFilters();
    
    // Add form reset functionality
    const resetButton = document.querySelector('a[href*="reports.dashboard"]');
    if (resetButton) {
        resetButton.addEventListener('click', function(e) {
            // Let the default link behavior work (navigating to the reset URL)
        });
    }

    // Initialize table container scroll behavior
    initTableScroll();

    // Add debug info
    console.log('Halaman3.js loaded successfully');
});

// Function to initialize filter inputs with proper event handlers
function initializeFilters() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const platInput = document.getElementById('plat_nomor');
    const merekInput = document.getElementById('merek');
    const resultSelect = document.getElementById('result');
    const filterForm = document.getElementById('filter-form');
    
    console.log('Initializing filters:', { 
        startDateExists: !!startDateInput,
        endDateExists: !!endDateInput,
        platInputExists: !!platInput,
        merekInputExists: !!merekInput,
        resultSelectExists: !!resultSelect,
        filterFormExists: !!filterForm
    });

    // Ensure dates are valid when submitting
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
                const startDate = new Date(startDateInput.value);
                const endDate = new Date(endDateInput.value);
                
                if (startDate > endDate) {
                    e.preventDefault();
                    showToast('Tanggal mulai tidak boleh lebih besar dari tanggal akhir', 'error');
                    return false;
                }
            }
            
            // Show loading state
            showLoadingIndicator();
        });
    }

    // Add auto-submit functionality to select inputs for better UX
    if (resultSelect) {
        resultSelect.addEventListener('change', function() {
            if (filterForm) {
                showLoadingIndicator();
                filterForm.submit();
            }
        });
    }

    // Add debounce to text inputs
    if (platInput) {
        addInputDebounce(platInput);
    }
    
    if (merekInput) {
        addInputDebounce(merekInput);
    }

    // Handle date range as a pair
    if (startDateInput && endDateInput) {
        // Update min date of end date when start date changes
        startDateInput.addEventListener('change', function() {
            if (this.value) {
                endDateInput.min = this.value;
                
                // If end date is now before start date, update it
                if (endDateInput.value && endDateInput.value < this.value) {
                    endDateInput.value = this.value;
                }
            }
        });

        // Update max date of start date when end date changes
        endDateInput.addEventListener('change', function() {
            if (this.value) {
                startDateInput.max = this.value;
                
                // If start date is now after end date, update it
                if (startDateInput.value && startDateInput.value > this.value) {
                    startDateInput.value = this.value;
                }
            }
        });

        // Auto-submit when both dates are filled
        const dateChangeHandler = function() {
            if (startDateInput.value && endDateInput.value) {
                setTimeout(() => {
                    if (filterForm) {
                        showLoadingIndicator();
                        filterForm.submit();
                    }
                }, 500);
            }
        };

        startDateInput.addEventListener('change', dateChangeHandler);
        endDateInput.addEventListener('change', dateChangeHandler);
    }
}

// Add debounced submit to text inputs
function addInputDebounce(input) {
    let timeout = null;
    
    input.addEventListener('input', function() {
        clearTimeout(timeout);
        
        timeout = setTimeout(() => {
            const form = input.closest('form');
            if (form && input.value.trim().length >= 2) {
                showLoadingIndicator();
                form.submit();
            }
        }, 800); // Wait for 800ms of inactivity before submitting
    });
}

// Show loading indicator when filtering
function showLoadingIndicator() {
    // Create or show a loading overlay
    let loadingIndicator = document.getElementById('filter-loading');
    if (!loadingIndicator) {
        loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'filter-loading';
        loadingIndicator.className = 'filter-loading-overlay';
        loadingIndicator.innerHTML = `
            <div class="bg-white p-5 rounded-lg flex flex-col items-center shadow-lg">
                <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
                <p class="mt-2 text-gray-700">Memuat data...</p>
            </div>
        `;
        document.body.appendChild(loadingIndicator);
    }
    
    // Show with animation
    setTimeout(() => {
        loadingIndicator.classList.add('show');
    }, 10);
}

// Function to handle table scrolling behavior
function initTableScroll() {
    const tableContainer = document.querySelector('.table-container');
    
    if (tableContainer) {
        const handleScroll = () => {
            const maxScrollLeft = tableContainer.scrollWidth - tableContainer.clientWidth;
            
            if (tableContainer.scrollLeft >= maxScrollLeft - 5) {
                tableContainer.classList.add('at-end');
            } else {
                tableContainer.classList.remove('at-end');
            }
        };
        
        tableContainer.addEventListener('scroll', handleScroll);
        
        // Initial check
        setTimeout(handleScroll, 100);
        
        // Add swipe hint animation on mobile
        if (window.innerWidth < 768) {
            const indicator = document.querySelector('.sticky-indicator');
            if (indicator) {
                setTimeout(() => {
                    indicator.style.opacity = '1';
                    setTimeout(() => {
                        indicator.style.opacity = '0.5';
                    }, 1000);
                }, 1000);
            }
        }
    }
}

// Function to show toast/notification messages - removed as we now use the central toast.js
// This was previously defined as:
// function showToast(message, type = 'success') {
//     // Create toast container if it doesn't exist
//     let toastContainer = document.getElementById('toast-container');
//     if (!toastContainer) {
//         toastContainer = document.createElement('div');
//         toastContainer.id = 'toast-container';
//         toastContainer.className = 'fixed top-4 right-4 z-50';
//         document.body.appendChild(toastContainer);
//     }
//     
//     // Create toast element
//     const toast = document.createElement('div');
//     toast.className = `mb-3 p-4 rounded-md shadow-md flex items-center ${
//         type === 'success' ? 'bg-green-100 text-green-800' : 
//         type === 'error' ? 'bg-red-100 text-red-800' : 
//         'bg-blue-100 text-blue-800'
//     }`;
//     
//     // Add icon based on type
//     const iconClass = type === 'success' ? 'fa-check-circle' : 
//                      type === 'error' ? 'fa-exclamation-circle' : 
//                      'fa-info-circle';
//     
//     toast.innerHTML = `
//         <i class="fas ${iconClass} mr-2"></i>
//         <span>${message}</span>
//         <button class="ml-auto text-gray-600 hover:text-gray-800 focus:outline-none">
//             <i class="fas fa-times"></i>
//         </button>
//     `;
//     
//     // Add close functionality
//     const closeButton = toast.querySelector('button');
//     closeButton.addEventListener('click', () => {
//         toast.remove();
//     });
//     
//     // Add to container
//     toastContainer.appendChild(toast);
//     
//     // Auto remove after 5 seconds
//     setTimeout(() => {
//         toast.remove();
//     }, 5000);
// } 