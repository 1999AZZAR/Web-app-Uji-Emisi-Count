(function() {
  let vehicles = [];
  let testedPlats = [];
  let filteredVehicles = []; // Store filtered results for better performance
  const pageSize = 10;
  let offset = 0;
  let totalVehicles = 0;
  let isLoading = false; // Track loading state
  let debugMode = true; // Enable for console logging

  /**
   * Debug logger function 
   */
  function debug(...args) {
    if (debugMode) {
      console.log(...args);
    }
  }

  /**
   * Show toast notification - removed as we now use the centralized toast.js
   */
  // function showToast(message, type = 'success', duration = 5000) {
  //   // Create toast container if it doesn't exist
  //   let toastContainer = document.getElementById('toast-container');
  //   if (!toastContainer) {
  //     toastContainer = document.createElement('div');
  //     toastContainer.id = 'toast-container';
  //     toastContainer.className = 'fixed top-4 right-4 z-50 flex flex-col items-end';
  //     document.body.appendChild(toastContainer);
  //   }
  //   
  //   // Create toast element
  //   const toast = document.createElement('div');
  //   toast.className = `mb-3 p-4 rounded-md shadow-md flex items-center transition-all transform translate-x-0 ${
  //     type === 'success' ? 'bg-green-100 text-green-800 border-l-4 border-green-500' : 
  //     type === 'error' ? 'bg-red-100 text-red-800 border-l-4 border-red-500' : 
  //     type === 'warning' ? 'bg-yellow-100 text-yellow-800 border-l-4 border-yellow-500' :
  //     'bg-blue-100 text-blue-800 border-l-4 border-blue-500'
  //   }`;
  //   
  //   // Add icon based on type
  //   const iconClass = type === 'success' ? 'fa-check-circle' : 
  //                    type === 'error' ? 'fa-exclamation-circle' : 
  //                    type === 'warning' ? 'fa-exclamation-triangle' :
  //                    'fa-info-circle';
  //   
  //   toast.innerHTML = `
  //     <i class="fas ${iconClass} mr-2"></i>
  //     <span>${message}</span>
  //     <button class="ml-auto text-gray-600 hover:text-gray-800 focus:outline-none">
  //       <i class="fas fa-times"></i>
  //     </button>
  //   `;
  //   
  //   // Add close functionality
  //   const closeButton = toast.querySelector('button');
  //   closeButton.addEventListener('click', () => {
  //     toast.classList.add('opacity-0', 'translate-x-full');
  //     setTimeout(() => toast.remove(), 300);
  //   });
  //   
  //   // Add animation
  //   toast.style.opacity = '0';
  //   toast.style.transform = 'translateX(100%)';
  //   
  //   // Add to container
  //   toastContainer.appendChild(toast);
  //   
  //   // Trigger animation
  //   setTimeout(() => {
  //     toast.style.opacity = '1';
  //     toast.style.transform = 'translateX(0)';
  //   }, 10);
  //   
  //   // Auto remove after duration
  //   setTimeout(() => {
  //     toast.classList.add('opacity-0', 'translate-x-full');
  //     setTimeout(() => toast.remove(), 300);
  //   }, duration);
  // }

  /**
   * Set loading state with spinner
   * @param {boolean} loading - Whether loading or not
   */
  function setLoading(loading) {
    isLoading = loading;
    
    // Get or create loading indicator
    let loadingIndicator = document.getElementById('loading-indicator');
    if (!loadingIndicator && loading) {
      loadingIndicator = document.createElement('div');
      loadingIndicator.id = 'loading-indicator';
      loadingIndicator.className = 'fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-40';
      loadingIndicator.innerHTML = `
        <div class="bg-white p-5 rounded-lg flex flex-col items-center">
          <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
          <p class="mt-2 text-gray-700">Loading...</p>
        </div>
      `;
      document.body.appendChild(loadingIndicator);
    } else if (!loading && loadingIndicator) {
      loadingIndicator.remove();
    }
  }

  /**
   * Fetch vehicles that have been tested
   * @returns {Promise} Promise that resolves when data is fetched
   */
  async function fetchTestedPlats() {
    try {
      const res = await fetch('/api/hasil-uji/tested-plats');
      if (!res.ok) {
        throw new Error(`Failed to fetch tested plates: ${res.status} ${res.statusText}`);
      }
      testedPlats = await res.json();
      debug('Tested plates loaded:', testedPlats.length);
      return testedPlats;
    } catch (e) {
      console.error('Error fetching tested plates:', e);
      showToast('Gagal memuat data kendaraan yang sudah diuji', 'error');
      return [];
    }
  }

  /**
   * Load vehicles with pagination
   * @param {number} off - Offset for pagination
   * @returns {Promise} Promise that resolves when data is fetched
   */
  async function loadVehicles(off = 0) {
    if (isLoading && off > 0) return;
    
    setLoading(true);
    try {
      debug('Loading vehicles, offset:', off);
      const res = await fetch(`/api/kendaraan-list?offset=${off}&limit=${pageSize}`);
      if (!res.ok) {
        throw new Error(`Failed to load vehicles: ${res.status} ${res.statusText}`);
      }
      
      const data = await res.json();
      debug('Vehicles loaded:', data.items.length, 'total:', data.total);
      
      if (off === 0) {
        // Reset for new search
        vehicles = data.items;
      } else {
        // Append for pagination
        vehicles = vehicles.concat(data.items);
      }
      
      totalVehicles = data.total;
      
      // Apply current filters and render
      applyFiltersAndRender();
      
      return data;
    } catch (e) {
      console.error('Error loading vehicles:', e);
      showToast('Gagal memuat data kendaraan', 'error');
      return null;
    } finally {
      setLoading(false);
    }
  }

  /**
   * Apply filters and render vehicle cards
   */
  function applyFiltersAndRender() {
    const platFilter = document.getElementById('filterPlat').value.toLowerCase();
    const merekFilter = document.getElementById('filterMerek').value;
    const tipeFilter = document.getElementById('filterTipe').value;
    const jenisFilter = document.getElementById('filterJenis').value;
    const testedFilter = document.getElementById('filterTested').value;

    debug('Applying filters:', { platFilter, merekFilter, tipeFilter, jenisFilter, testedFilter });
    debug('Vehicles before filtering:', vehicles.length);
    
    // Apply filters
    filteredVehicles = vehicles.filter(v => {
      const isTested = testedPlats.includes(v.plat_nomor);
      
      if (platFilter && !v.plat_nomor.toLowerCase().includes(platFilter)) return false;
      if (merekFilter && v.merek !== merekFilter) return false;
      if (tipeFilter && v.tipe !== tipeFilter) return false;
      if (jenisFilter && v.jenis !== jenisFilter) return false;
      if (testedFilter === 'tested' && !isTested) return false;
      if (testedFilter === 'untested' && isTested) return false;
      
      return true;
    });

    debug('Filtered vehicles:', filteredVehicles.length);
    renderCards();
  }

  /**
   * Render vehicle cards based on filtered data
   */
  function renderCards() {
    const container = document.getElementById('vehicleCards');
    if (!container) {
      console.error('Vehicle cards container not found');
      return;
    }
    
    debug('Rendering cards, filtered count:', filteredVehicles.length);
    
    // Show no results message if needed
    if (filteredVehicles.length === 0) {
      container.innerHTML = `
        <div class="col-span-3 py-8 flex flex-col items-center text-gray-500">
          <i class="fas fa-search text-4xl mb-2"></i>
          <p>No vehicles found matching your criteria</p>
        </div>
      `;
      document.getElementById('loadMoreContainer').classList.add('hidden');
      return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Add cards
    filteredVehicles.forEach(v => {
      const isTested = testedPlats.includes(v.plat_nomor);
      const card = document.createElement('div');
      card.className = 'bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-1';
      card.innerHTML = `
        <div class="border-t-4 ${isTested ? 'border-green-500' : 'border-primary'}"></div>
        <div class="p-4 flex flex-col flex-grow">
          <div class="flex justify-between items-center">
            <h3 class="font-medium text-lg text-gray-800">${v.plat_nomor}</h3>
            <span class="text-sm font-medium ${isTested ? 'text-green-600' : 'text-red-600'}">
              ${isTested ? '<i class="fas fa-check-circle"></i> Tested' : '<i class="fas fa-times-circle"></i> Not Tested'}
            </span>
          </div>
          <div class="mt-2 space-y-1 text-gray-600 text-sm">
            <p><i class="fas fa-tags mr-1"></i>${v.merek || 'N/A'} ${v.tipe || ''}</p>
            <p><i class="fas fa-calendar-alt mr-1"></i>${v.tahun || 'N/A'}</p>
            <p><i class="fas fa-car-side mr-1"></i>${v.jenis || 'N/A'}</p>
            <p>${v.fuel_type === 'solar' ? 
              '<i class="fas fa-gas-pump text-blue-600 mr-1"></i><span class="font-medium text-blue-600">Solar</span>' : 
              '<i class="fas fa-gas-pump text-green-600 mr-1"></i><span class="font-medium text-green-600">Bensin</span>'}</p>
            <p><i class="fas fa-weight-hanging mr-1"></i>${v.fuel_type === 'solar' 
              ? (v.load_category === '<3.5ton' ? '< 3.5 Ton' : '≥ 3.5 Ton')
              : (v.load_category === 'kendaraan_muatan' ? 'Kendaraan Muatan' : 'Kendaraan Penumpang')}</p>
            <p><i class="fas fa-building mr-1"></i>${v.nama_instansi || '-'}</p>
          </div>
        </div>
        <div class="bg-gray-50 px-4 py-2 flex justify-end space-x-2">
          <button class="delete-btn text-gray-500 hover:text-red-500 p-2 transition-colors" title="Hapus" data-plat="${v.plat_nomor}">
            <i class="fas fa-trash"></i>
          </button>
          <button class="test-btn text-gray-500 hover:text-blue-500 p-2 transition-colors" title="${isTested ? 'Edit Data' : 'Add Data'}" data-plat="${v.plat_nomor}">
            <i class="${isTested ? 'fas fa-edit' : 'fas fa-vial'}"></i>
          </button>
        </div>`;
      container.appendChild(card);
    });

    // Show/hide load more button
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    if (loadMoreContainer) {
      if (vehicles.length < totalVehicles) {
        loadMoreContainer.classList.remove('hidden');
      } else {
        loadMoreContainer.classList.add('hidden');
      }
    }

    // Attach event handlers
    attachEvents();
  }

  /**
   * Show test form modal
   * @param {string} plat - License plate number
   */
  async function showForm(plat) {
    setLoading(true);
    
    const modal = document.getElementById('testModal');
    const clearBtn = document.getElementById('clearBtn');
    const confirmModal = document.getElementById('confirmModal');
    const opacityField = document.getElementById('opacityField');
    const opacityInput = document.getElementById('opacity');
    const formFields = document.querySelectorAll('#hasilUjiForm .form-field:not(#opacityField)');
    const form = document.getElementById('hasilUjiForm');
    const hasil = document.getElementById('hasil');
    const hasilUjiForm = document.getElementById('hasilUjiForm');
    
    // Reset form and UI state
    form.reset();
    clearBtn.classList.add('hidden');
    formFields.forEach(field => field.classList.remove('hidden'));
    opacityField.classList.add('hidden');
    opacityInput.required = false;
    hasil.classList.add('hidden');
    
    // Set up clear button
    clearBtn.onclick = () => {
      document.getElementById('confirmText').textContent = `Hapus data uji ${plat}?`;
      confirmModal.classList.remove('hidden');
      document.getElementById('confirmYes').onclick = async () => {
        try {
          setLoading(true);
          const res = await fetch(`/api/hasil-uji/${plat}`, { method: 'DELETE' });
          if (!res.ok) throw new Error(`Failed to delete test data: ${res.status}`);
          
          showToast('Data uji berhasil dihapus', 'success'); 
          await fetchTestedPlats();
          applyFiltersAndRender();
          modal.classList.add('hidden');
        } catch (error) {
          console.error('Error deleting test data:', error);
          showToast('Gagal menghapus data uji', 'error');
        } finally {
          setLoading(false);
          confirmModal.classList.add('hidden');
        }
      };
    };
    
    try {
      // Get vehicle details to check fuel type
      const vehicleRes = await fetch(`/api/kendaraan/${plat}`);
      if (!vehicleRes.ok) throw new Error(`Failed to fetch vehicle: ${vehicleRes.status}`);
      
      const vehicle = await vehicleRes.json();
      const isSolar = vehicle.fuel_type === 'solar';
      
      // Show/hide fields based on fuel type
      if (isSolar) {
        // For diesel: show only opacity field
        formFields.forEach(field => field.classList.add('hidden'));
        opacityField.classList.remove('hidden');
        opacityInput.required = true;
      } else {
        // For petrol: show all fields except opacity
        formFields.forEach(field => field.classList.remove('hidden'));
        opacityField.classList.add('hidden');
        opacityInput.required = false;
      }
      
      // Update vehicle info display
      document.getElementById('kendaraan_detail').innerHTML = `
        <strong>${plat}</strong> - ${vehicle.merek} ${vehicle.tipe} (${vehicle.tahun}) - 
        ${vehicle.fuel_type === 'solar' ? 'Solar' : 'Bensin'}`;
      
      // Try to load existing test results
      const resultsRes = await fetch(`/api/hasil-uji/${plat}`);
      if (resultsRes.ok) {
        const data = await resultsRes.json();
        
        // Populate form with existing data
        ['co', 'co2', 'hc', 'o2', 'lambda', 'opacity'].forEach(id => {
          const element = document.getElementById(id);
          if (element && data[id] !== undefined) {
            element.value = data[id] !== null ? data[id] : '';
          }
        });
        
        // Show results section and clear button
        hasil.classList.remove('hidden');
        clearBtn.classList.remove('hidden');
        
        // Show validation result
        const validasi = document.getElementById('validasi');
        const kelulusan = document.getElementById('kelulusan');
        
        validasi.innerHTML = `
          <span class="font-medium">Validasi:</span> 
          <span class="${data.valid ? 'text-green-600' : 'text-red-600'}">
            ${data.valid ? '<i class="fas fa-check-circle"></i> Valid' : '<i class="fas fa-times-circle"></i> Tidak Valid'}
          </span>`;
          
        kelulusan.innerHTML = `
          <span class="font-medium">Kelulusan:</span>
          <span class="${data.lulus ? 'text-green-600' : 'text-red-600'}">
            ${data.lulus ? '<i class="fas fa-check-circle"></i> Lulus' : '<i class="fas fa-times-circle"></i> Tidak Lulus'}
          </span>`;
      } else {
        // No existing data - reset form
        form.reset();
        clearBtn.classList.add('hidden');
        hasil.classList.add('hidden');
      }
      
      // Set up form submission
      hasilUjiForm.onsubmit = async (e) => {
        e.preventDefault();
        
        try {
          const payload = {};
          if (isSolar) {
            // For diesel vehicles
            if (!opacityInput.value) {
              showToast('Nilai Opasitas harus diisi untuk kendaraan solar', 'error');
              return;
            }
            
            // Default values for required fields
            payload.co = 0;
            payload.co2 = 0;
            payload.hc = 0;
            payload.o2 = 0;
            payload.lambda_val = 0;
            payload.opacity = parseFloat(opacityInput.value);
          } else {
            // For petrol vehicles
            const co = document.getElementById('co').value;
            const co2 = document.getElementById('co2').value;
            const hc = document.getElementById('hc').value;
            const o2 = document.getElementById('o2').value;
            const lambda = document.getElementById('lambda').value;
            
            // Validate required fields
            const missingFields = [];
            if (!co) missingFields.push('CO');
            if (!co2) missingFields.push('CO2');
            if (!hc) missingFields.push('HC');
            if (!o2) missingFields.push('O2');
            if (!lambda) missingFields.push('Lambda');
            
            if (missingFields.length > 0) {
              showToast(`Nilai ${missingFields.join(', ')} harus diisi`, 'error');
              return;
            }
            
            payload.co = parseFloat(co);
            payload.co2 = parseFloat(co2);
            payload.hc = parseInt(hc, 10);
            payload.o2 = parseFloat(o2);
            payload.lambda_val = parseFloat(lambda);
            payload.opacity = null;
          }
          
          setLoading(true);
          
          const rsp = await fetch(`/api/hasil-uji/${plat}`, {
            method: 'POST', 
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
          });
          
          const result = await rsp.json();
          
          if (rsp.ok) {
            // Format success message
            const status = [];
            if (result.valid !== undefined) {
              status.push(`Valid: ${result.valid ? 'Ya' : 'Tidak'}`);
            }
            if (result.lulus !== undefined) {
              status.push(`Lulus: ${result.lulus ? 'Ya' : 'Tidak'}`);
            }
            if (result.operator) {
              status.push(`Operator: ${result.operator}`);
            }
            
            showToast(`Data berhasil disimpan – ${status.join(', ')}`, 'success');
            await fetchTestedPlats();
            applyFiltersAndRender();
            modal.classList.add('hidden');
          } else {
            showToast(`Gagal menyimpan data: ${result.error || 'Unknown error'}`, 'error');
          }
        } catch (error) {
          console.error('Error saving test results:', error);
          showToast('Terjadi kesalahan saat menyimpan data', 'error');
        } finally {
          setLoading(false);
        }
      };
      
      // Show modal
      modal.classList.remove('hidden');
    } catch (error) {
      console.error('Error preparing test form:', error);
      showToast('Gagal mempersiapkan form pengujian', 'error');
    } finally {
      setLoading(false);
    }
  }

  /**
   * Attach event handlers to vehicle cards
   */
  function attachEvents() {
    // Delete vehicle buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
      btn.onclick = () => {
        const plat = btn.dataset.plat;
        document.getElementById('confirmText').textContent = `Hapus kendaraan ${plat}?`;
        const confirmModal = document.getElementById('confirmModal');
        confirmModal.classList.remove('hidden');
        
        document.getElementById('confirmYes').onclick = async () => {
          try {
            setLoading(true);
            const res = await fetch(`/api/kendaraan/${plat}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`Failed to delete vehicle: ${res.status}`);
            
            // Refresh data
            await fetchTestedPlats();
            await loadVehicles(0); // Reset to first page
            showToast('Kendaraan berhasil dihapus', 'success');
          } catch (error) {
            console.error('Error deleting vehicle:', error);
            showToast('Gagal menghapus kendaraan', 'error');
          } finally {
            setLoading(false);
            confirmModal.classList.add('hidden');
          }
        };
      };
    });

    // Test buttons
    document.querySelectorAll('.test-btn').forEach(btn => {
      btn.onclick = () => showForm(btn.dataset.plat);
    });
  }

  /**
   * Initialize form fields for debounce
   */
  function initializeFormFields() {
    // Add debounce to search input for better performance
    let searchTimeout = null;
    const filterPlat = document.getElementById('filterPlat');
    if (filterPlat) {
      filterPlat.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          applyFiltersAndRender();
        }, 300); // 300ms debounce
      });
    }
    
    // Add event listeners to other filters
    ['filterMerek', 'filterTipe', 'filterJenis', 'filterTested'].forEach(id => {
      const element = document.getElementById(id);
      if (element) {
        element.addEventListener('change', applyFiltersAndRender);
      } else {
        debug(`Warning: Filter element ${id} not found`);
      }
    });
  }

  /**
   * Initialize the page
   */
  async function init() {
    try {
      debug('Initializing halaman2.js');
      setLoading(true);
      
      // Set up modal close handlers
      const modalClose = document.getElementById('modalClose');
      if (modalClose) {
        modalClose.onclick = () => {
          document.getElementById('testModal').classList.add('hidden');
        };
      }
      
      const confirmModal = document.getElementById('confirmModal');
      const confirmClose = document.getElementById('confirmClose');
      const confirmNo = document.getElementById('confirmNo');
      
      if (confirmClose) {
        confirmClose.onclick = () => confirmModal.classList.add('hidden');
      }
      
      if (confirmNo) {
        confirmNo.onclick = () => confirmModal.classList.add('hidden');
      }
      
      // Initialize load more button
      const loadMoreBtn = document.getElementById('loadMoreBtn');
      if (loadMoreBtn) {
        loadMoreBtn.onclick = () => {
          offset += pageSize;
          loadVehicles(offset);
        };
      }
      
      // Initialize form fields
      initializeFormFields();
      
      // Close modals when clicking outside
      const modals = document.querySelectorAll('#testModal, #confirmModal');
      modals.forEach(modal => {
        if (modal) {
          modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
          });
        }
      });
      
      // Fetch dropdown data in parallel
      const merekPromise = fetch('/api/kendaraan-mereks').then(res => {
        if (!res.ok) throw new Error(`Error fetching mereks: ${res.status}`);
        return res.json();
      });
      
      const tipePromise = fetch('/api/kendaraan-tipes').then(res => {
        if (!res.ok) throw new Error(`Error fetching tipes: ${res.status}`);
        return res.json();
      });
      
      // Load initial data
      debug('Fetching tested plates...');
      await fetchTestedPlats();
      
      debug('Fetching vehicles...');
      const vehiclesData = await loadVehicles(0);
      
      if (!vehiclesData || !vehiclesData.items || vehiclesData.items.length === 0) {
        debug('No vehicles returned from API');
        showToast('Tidak ada data kendaraan yang ditemukan', 'info');
      }
      
      // Populate dropdown menus
      try {
        const [mereks, tipes] = await Promise.all([merekPromise, tipePromise]);
        
        const merekSelect = document.getElementById('filterMerek');
        if (merekSelect && mereks && mereks.length) {
          mereks.forEach(merek => {
            const opt = document.createElement('option');
            opt.value = merek;
            opt.textContent = merek;
            merekSelect.appendChild(opt);
          });
        }
        
        const tipeSelect = document.getElementById('filterTipe');
        if (tipeSelect && tipes && tipes.length) {
          tipes.forEach(tipe => {
            const opt = document.createElement('option');
            opt.value = tipe;
            opt.textContent = tipe;
            tipeSelect.appendChild(opt);
          });
        }
      } catch (error) {
        debug('Error loading dropdown data:', error);
        showToast('Error loading filter options', 'warning');
      }
      
    } catch (error) {
      console.error('Error initializing page:', error);
      showToast('Terjadi kesalahan saat memuat halaman', 'error');
    } finally {
      setLoading(false);
    }
  }

  // Initialize when DOM is loaded
  document.addEventListener('DOMContentLoaded', init);
})();
