document.addEventListener('DOMContentLoaded', function() {
    const loadCategorySelect = document.getElementById('load_category');
    const fuelTypeRadios = document.querySelectorAll('.fuel-type-radio');
    const jenisSelect = document.getElementById('jenis');
    const instansiDiv = document.getElementById('instansi_div');
    const instansiInput = document.getElementById('nama_instansi');
    const kendaraanForm = document.getElementById('kendaraanForm');
    const submitBtn = document.getElementById('submitBtn');
    const formStatus = document.getElementById('formStatus');
    const errorElements = document.querySelectorAll('.error-message');

    // Define load categories based on fuel type
    const loadCategories = {
        bensin: ['kendaraan_muatan', 'kendaraan_penumpang'],
        solar: ['<3.5ton', '>=3.5ton']
    };
    
    // Define display names for load categories
    const categoryDisplayNames = {
        'kendaraan_muatan': 'Kendaraan Muatan',
        'kendaraan_penumpang': 'Kendaraan Penumpang',
        '<3.5ton': 'Kurang dari 3.5 Ton',
        '>=3.5ton': 'Lebih dari atau sama dengan 3.5 Ton'
    };

    // Function to clear all error messages
    function clearErrors() {
        errorElements.forEach(el => {
            el.textContent = '';
            el.classList.add('hidden');
        });
    }

    // Function to show an error message for a specific field
    function showError(fieldId, message) {
        const errorElement = document.getElementById(`${fieldId}-error`);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
            // Also highlight the input field
            const inputField = document.getElementById(fieldId);
            if (inputField) {
                inputField.classList.add('border-red-500');
                inputField.focus();
            }
        }
    }

    // Function to update load categories
    function updateLoadCategories() {
        const selectedFuelType = document.querySelector('.fuel-type-radio:checked').value;
        
        // Clear existing options
        loadCategorySelect.innerHTML = '';
        
        // Add placeholder option
        const placeholderOption = document.createElement('option');
        placeholderOption.value = '';
        placeholderOption.textContent = 'Pilih Kategori Beban';
        placeholderOption.disabled = true;
        placeholderOption.selected = true;
        loadCategorySelect.appendChild(placeholderOption);
        
        // Add new options based on fuel type
        loadCategories[selectedFuelType].forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = categoryDisplayNames[category];
            loadCategorySelect.appendChild(option);
        });
    }

    function updateInstansiFieldVisibility() {
        if (jenisSelect.value === 'dinas') {
            instansiDiv.classList.remove('hidden');
            if (instansiInput.value === '-') { // Jika sebelumnya diset ke placeholder '-' (misal dari pilihan 'Umum')
                instansiInput.value = '';      // Kosongkan agar pengguna bisa input nama instansi
            }
            instansiInput.setAttribute('required', 'required');
        } else {
            instansiDiv.classList.add('hidden');
            instansiInput.value = '-'; // Set to hyphen when hidden or for 'Umum'
            instansiInput.removeAttribute('required');
        }
    }

    // Add change event listener to radio buttons
    fuelTypeRadios.forEach(radio => {
        radio.addEventListener('change', updateLoadCategories);
        // Clear error when user changes selection
        radio.addEventListener('change', () => {
            document.getElementById('fuel_type-error').classList.add('hidden');
        });
    });

    // Initial setup
    updateLoadCategories();
    
    if (jenisSelect) {
        // Initial setup in case of page reload with a value selected
        updateInstansiFieldVisibility();
        
        jenisSelect.addEventListener('change', updateInstansiFieldVisibility);
        // Clear error when user changes selection
        jenisSelect.addEventListener('change', () => {
            document.getElementById('jenis-error').classList.add('hidden');
        });
    }

    // Clear error when user makes changes to the field
    document.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('input', () => {
            input.classList.remove('border-red-500');
            const fieldId = input.id;
            const errorElement = document.getElementById(`${fieldId}-error`);
            if (errorElement) {
                errorElement.classList.add('hidden');
            }
        });
    });

    if (kendaraanForm) {
        kendaraanForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            clearErrors();
            
            // Disable submit button and show loading state
            submitBtn.disabled = true;
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Menyimpan...';
            formStatus.textContent = '';
            formStatus.className = 'text-sm';
            
            try {
                // Validate all required fields
                const formData = new FormData(this);
                let hasError = false;
                
                // Check if jenis is selected
                if (!formData.get('jenis')) {
                    showError('jenis', 'Jenis kendaraan harus dipilih');
                    hasError = true;
                }
                
                // Check plat_nomor
                const plat = formData.get('plat_nomor').trim().toUpperCase();
                if (!plat || plat.length < 4) {
                    showError('plat_nomor', 'Format nomor polisi tidak valid (min. 4 karakter)');
                    hasError = true;
                }
                
                // Check merek
                if (!formData.get('merek').trim()) {
                    showError('merek', 'Merek tidak boleh kosong');
                    hasError = true;
                }
                
                // Check tipe
                if (!formData.get('tipe').trim()) {
                    showError('tipe', 'Tipe tidak boleh kosong');
                    hasError = true;
                }
                
                // Check tahun
                const tahun = parseInt(formData.get('tahun'));
                if (isNaN(tahun) || tahun < 1900 || tahun > 2100) {
                    showError('tahun', 'Tahun harus di antara 1900 dan 2100');
                    hasError = true;
                }
                
                // Check load_category
                if (!formData.get('load_category')) {
                    showError('load_category', 'Kategori beban harus dipilih');
                    hasError = true;
                }
                
                // Check nama_instansi for dinas vehicles
                if (formData.get('jenis') === 'dinas' && !formData.get('nama_instansi').trim()) {
                    showError('nama_instansi', 'Nama instansi harus diisi untuk kendaraan dinas');
                    hasError = true;
                }
                
                if (hasError) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                    return;
                }

                // Prepare data for API
                const data = {
                    jenis: formData.get('jenis'),
                    plat_nomor: plat,
                    merek: formData.get('merek').trim(),
                    tipe: formData.get('tipe').trim(),
                    tahun: tahun,
                    fuel_type: formData.get('fuel_type'),
                    nama_instansi: formData.get('nama_instansi').trim() || '-',
                    load_category: formData.get('load_category')
                };

                // Send request
                const response = await fetch('/api/kendaraan', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                
                if (response.ok && result.success) {
                    // Show success message
                    formStatus.textContent = 'Data kendaraan berhasil disimpan!';
                    formStatus.className = 'text-sm text-green-600';
                    
                    // Reset form
                    this.reset();
                    updateLoadCategories();
                    updateInstansiFieldVisibility();
                    
                    // Optionally redirect after success
                    // window.location.href = '/halaman2';
                } else {
                    const errorMsg = result.error || 'Gagal menyimpan data kendaraan.';
                    formStatus.textContent = errorMsg;
                    formStatus.className = 'text-sm text-red-600';
                    
                    // If error is about duplicate plate number
                    if (response.status === 409) {
                        showError('plat_nomor', 'Nomor plat sudah terdaftar');
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                formStatus.textContent = 'Terjadi kesalahan saat menyimpan data.';
                formStatus.className = 'text-sm text-red-600';
            } finally {
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    }

    // Batch upload handling
    const batchFileInput = document.getElementById('batchFile');
    const uploadBtn = document.getElementById('uploadBtn');
    const batchResult = document.getElementById('batchResult');
    const batchSummary = document.getElementById('batchSummary');
    const batchErrors = document.getElementById('batchErrors');
    
    if (uploadBtn) {
        uploadBtn.addEventListener('click', async function() {
            const file = batchFileInput.files[0];
            if (!file) { 
                showToast('Pilih file CSV terlebih dahulu.', 'error'); 
                return; 
            }
            
            // Disable button and show loading state
            uploadBtn.disabled = true;
            const originalBtnText = uploadBtn.innerHTML;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Mengupload...';
            
            // Hide previous results
            batchResult.classList.add('hidden');
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const res = await fetch('/api/kendaraan/batch-upload', { 
                    method: 'POST', 
                    body: formData 
                });
                
                const result = await res.json();
                
                // Show result area
                batchResult.classList.remove('hidden');
                
                if (res.ok) {
                    let summaryMsg = `Berhasil: ${result.successes} kendaraan`;
                    
                    if (result.errors && result.errors.length) {
                        summaryMsg += `; ${result.errors.length} kendaraan gagal`;
                        
                        // Show detailed error list
                        batchErrors.classList.remove('hidden');
                        batchErrors.innerHTML = '<div class="font-semibold mb-2">Detail Kesalahan:</div>';
                        
                        result.errors.forEach(error => {
                            const errorItem = document.createElement('div');
                            errorItem.className = 'text-sm text-red-700 mb-1 p-1 border-b border-red-200';
                            errorItem.textContent = `Baris ${error.row}: ${error.error}`;
                            batchErrors.appendChild(errorItem);
                        });
                    } else {
                        batchErrors.classList.add('hidden');
                    }
                    
                    batchSummary.textContent = summaryMsg;
                    batchSummary.className = 'text-sm bg-green-100 p-2 rounded';
                    
                    // Reset file input
                    batchFileInput.value = '';
                } else {
                    batchSummary.textContent = result.error || 'Gagal upload CSV.';
                    batchSummary.className = 'text-sm bg-red-100 p-2 rounded';
                    batchErrors.classList.add('hidden');
                }
            } catch (e) {
                console.error(e);
                batchResult.classList.remove('hidden');
                batchSummary.textContent = 'Terjadi kesalahan saat upload.';
                batchSummary.className = 'text-sm bg-red-100 p-2 rounded';
                batchErrors.classList.add('hidden');
            } finally {
                // Re-enable button
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = originalBtnText;
            }
        });
    }
}); 