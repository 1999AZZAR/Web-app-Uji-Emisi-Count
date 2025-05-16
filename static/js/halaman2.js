(function() {
  let vehicles = [];
  let testedPlats = [];
  const pageSize = 10;
  let offset = 0;
  let totalVehicles = 0;

  async function fetchTestedPlats() {
    try {
      const res = await fetch('/api/hasil-uji/tested-plats');
      testedPlats = res.ok ? await res.json() : [];
    } catch (e) {
      console.error(e);
    }
  }

  async function loadVehicles(off) {
    try {
      const res = await fetch(`/api/kendaraan-list?offset=${off}&limit=${pageSize}`);
      if (res.ok) {
        const data = await res.json();
        vehicles = vehicles.concat(data.items);
        totalVehicles = data.total;
        renderCards();
      }
    } catch (e) {
      console.error(e);
    }
  }

  function renderCards() {
    const container = document.getElementById('vehicleCards');
    container.innerHTML = '';
    const platFilter = document.getElementById('filterPlat').value.toLowerCase();
    const merekFilter = document.getElementById('filterMerek').value;
    const tipeFilter = document.getElementById('filterTipe').value;
    const jenisFilter = document.getElementById('filterJenis').value;
    const testedFilter = document.getElementById('filterTested').value;

    vehicles.filter(v => {
      const isTested = testedPlats.includes(v.plat_nomor);
      if (platFilter && !v.plat_nomor.toLowerCase().includes(platFilter)) return false;
      if (merekFilter && v.merek !== merekFilter) return false;
      if (tipeFilter && v.tipe !== tipeFilter) return false;
      if (jenisFilter && v.jenis !== jenisFilter) return false;
      if (testedFilter === 'tested' && !isTested) return false;
      if (testedFilter === 'untested' && isTested) return false;
      return true;
    }).forEach(v => {
      const isTested = testedPlats.includes(v.plat_nomor);
      const card = document.createElement('div');
      card.className = 'bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300 transform hover:-translate-y-1';
      card.innerHTML = `
        <div class="border-t-4 border-primary"></div>
        <div class="p-4 flex flex-col flex-grow">
          <div class="flex justify-between items-center">
            <h3 class="font-medium text-lg text-gray-800">${v.plat_nomor}</h3>
            <span class="text-sm font-medium ${isTested ? 'text-green-600' : 'text-red-600'}">
              ${isTested ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-times-circle"></i>'}
            </span>
          </div>
          <div class="mt-2 space-y-1 text-gray-600 text-sm">
            <p><i class="fas fa-tags mr-1"></i>${v.merek} ${v.tipe}</p>
            <p><i class="fas fa-calendar-alt mr-1"></i>${v.tahun}</p>
            <p><i class="fas fa-car-side mr-1"></i>${v.jenis}</p>
            <p><i class="fas fa-fuel-pump mr-1"></i>${v.fuel_type === 'diesel' ? 'Diesel' : 'Bensin'}</p>
            <p><i class="fas fa-weight-hanging mr-1"></i>${v.fuel_type === 'diesel' 
              ? (v.load_category === '<3.5ton' ? '< 3.5 Ton' : '≥ 3.5 Ton')
              : (v.load_category === 'kendaraan_muatan' ? 'Kendaraan Muatan' : 'Kendaraan Penumpang')}</p>
            <p><i class="fas fa-building mr-1"></i>${v.nama_instansi || '-'}</p>
          </div>
        </div>
        <div class="bg-gray-50 px-4 py-2 flex justify-end space-x-2">
          <button class="delete-btn text-gray-500 hover:text-red-500 p-2" title="Hapus" data-plat="${v.plat_nomor}">
            <i class="fas fa-trash"></i>
          </button>
          <button class="test-btn text-gray-500 hover:text-blue-500 p-2" title="${isTested ? 'Edit Data' : 'Add Data'}" data-plat="${v.plat_nomor}">
            <i class="${isTested ? 'fas fa-edit' : 'fas fa-vial'}"></i>
          </button>
        </div>`;
      container.appendChild(card);
    });

    const loadMoreContainer = document.getElementById('loadMoreContainer');
    if (vehicles.length < totalVehicles) loadMoreContainer.classList.remove('hidden'); else loadMoreContainer.classList.add('hidden');

    attachEvents();
  }

  async function showForm(plat) {
    const modal = document.getElementById('testModal');
    const clearBtn = document.getElementById('clearBtn');
    const confirmModal = document.getElementById('confirmModal');
    const opacityField = document.getElementById('opacityField');
    const opacityInput = document.getElementById('opacity');
    const formFields = document.querySelectorAll('#hasilUjiForm .form-field:not(#opacityField)');
    
    // Reset form and UI state
    clearBtn.classList.add('hidden');
    formFields.forEach(field => field.classList.remove('hidden'));
    opacityField.classList.add('hidden');
    opacityInput.required = false;
    
    clearBtn.onclick = () => {
      document.getElementById('confirmText').textContent = `Hapus data uji ${plat}?`;
      confirmModal.classList.remove('hidden');
      document.getElementById('confirmYes').onclick = async () => {
        const res = await fetch(`/api/hasil-uji/${plat}`, { method: 'DELETE' });
        if (res.ok) {
          showToast('Data uji dihapus', 'success'); 
          fetchTestedPlats().then(() => loadVehicles(offset)); 
          modal.classList.add('hidden');
        } else {
          showToast('Gagal menghapus data uji', 'error');
        }
        confirmModal.classList.add('hidden');
      };
    };
    
    // Get vehicle details to check fuel type
    try {
      const vehicleRes = await fetch(`/api/kendaraan/${plat}`);
      if (vehicleRes.ok) {
        const vehicle = await vehicleRes.json();
        const isDiesel = vehicle.fuel_type === 'diesel';
        
        // Show/hide fields based on fuel type
        if (isDiesel) {
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
      }
    } catch (error) {
      console.error('Error fetching vehicle details:', error);
      showToast('Gagal memuat detail kendaraan', 'error');
    }
    
    modal.classList.remove('hidden');
    document.getElementById('kendaraan_detail').textContent = plat;
    const info = document.getElementById('kendaraan_info');
    info.style.display = 'block';
    const form = document.getElementById('hasilUjiForm');
    form.style.display = 'block';
    document.getElementById('hasil').classList.add('hidden');
    
    // Load existing test results if any
    const res = await fetch(`/api/hasil-uji/${plat}`);
    if (res.ok) {
      const data = await res.json();
      // Set values for all fields including opacity
      ['co', 'co2', 'hc', 'o2', 'lambda', 'opacity'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.value = data[id] || '';
      });
      
      document.getElementById('hasil').classList.remove('hidden');
      clearBtn.classList.remove('hidden');
    } else {
      form.reset();
      clearBtn.classList.add('hidden');
    }
    form.onsubmit = async e => {
      e.preventDefault();
      const payload = {};
      const isDiesel = !opacityField.classList.contains('hidden');
      
      if (isDiesel) {
        // For diesel: only include opacity
        if (!opacityInput.value) {
          showToast('Opasitas diperlukan untuk kendaraan diesel', 'error');
          return;
        }
        // Set default values for other fields as they are required in the database
        payload.co = 0;
        payload.co2 = 0;
        payload.hc = 0;
        payload.o2 = 0;
        payload.lambda_val = 0;
        payload.opacity = parseFloat(opacityInput.value);
      } else {
        // For petrol: include all other fields
        const co = document.getElementById('co').value;
        const co2 = document.getElementById('co2').value;
        const hc = document.getElementById('hc').value;
        const o2 = document.getElementById('o2').value;
        const lambda = document.getElementById('lambda').value;
        
        // Validate required fields for petrol vehicles
        if (!co || !co2 || !hc || !o2 || !lambda) {
          showToast('Semua field harus diisi untuk kendaraan bensin', 'error');
          return;
        }
        
        payload.co = parseFloat(co);
        payload.co2 = parseFloat(co2);
        payload.hc = parseInt(hc, 10);
        payload.o2 = parseFloat(o2);
        payload.lambda_val = parseFloat(lambda);
        payload.opacity = null; // Explicitly set to null for petrol vehicles
      }
      
      try {
        const rsp = await fetch(`/api/hasil-uji/${plat}`, {
          method: 'POST', 
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        
        const result = await rsp.json();
        
        if (rsp.ok) {
          const status = [];
          if (result.valid !== undefined) status.push(`Valid: ${result.valid ? 'Ya' : 'Tidak'}`);
          if (result.lulus !== undefined) status.push(`Lulus: ${result.lulus ? 'Ya' : 'Tidak'}`);
          if (result.operator) status.push(`Operator: ${result.operator}`);
          
          showToast(`Tersimpan – ${status.join(', ')}`, 'success');
          fetchTestedPlats().then(() => loadVehicles(offset)); 
          modal.classList.add('hidden');
        } else {
          showToast(`Gagal menyimpan data: ${result.error || 'Tidak ada pesan kesalahan'}`, 'error');
        }
      } catch (error) {
        console.error('Error saving test results:', error);
        showToast('Terjadi kesalahan saat menyimpan data', 'error');
      }
    };
  }

  function attachEvents() {
    document.querySelectorAll('.delete-btn').forEach(btn => {
      btn.onclick = () => {
        const plat = btn.dataset.plat;
        document.getElementById('confirmText').textContent = `Hapus kendaraan ${plat}?`;
        const confirmModal = document.getElementById('confirmModal');
        confirmModal.classList.remove('hidden');
        document.getElementById('confirmYes').onclick = async () => {
          const res = await fetch(`/api/kendaraan/${plat}`, { method: 'DELETE' });
          if (res.ok) {
            fetchTestedPlats().then(() => loadVehicles(offset)); showToast('Kendaraan dihapus', 'success');
          } else showToast('Gagal menghapus kendaraan', 'error');
          confirmModal.classList.add('hidden');
        };
      };
    });

    document.querySelectorAll('.test-btn').forEach(btn => {
      btn.onclick = () => showForm(btn.dataset.plat);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('modalClose').onclick = () => document.getElementById('testModal').classList.add('hidden');
    const confirmModal = document.getElementById('confirmModal');
    document.getElementById('confirmClose').onclick = () => confirmModal.classList.add('hidden');
    document.getElementById('confirmNo').onclick = () => confirmModal.classList.add('hidden');
    fetchTestedPlats().then(() => loadVehicles(offset));
    fetch('/api/kendaraan-mereks').then(res => res.json()).then(items => {
      const sel = document.getElementById('filterMerek');
      items.forEach(m => { const opt=document.createElement('option'); opt.value=m; opt.textContent=m; sel.appendChild(opt); });
    });
    fetch('/api/kendaraan-tipes').then(res => res.json()).then(items => {
      const sel = document.getElementById('filterTipe');
      items.forEach(t => { const opt=document.createElement('option'); opt.value=t; opt.textContent=t; sel.appendChild(opt); });
    });
    ['filterPlat','filterMerek','filterTipe','filterJenis','filterTested'].forEach(id => {
      document.getElementById(id).addEventListener('change', renderCards);
    });
    document.getElementById('loadMoreBtn').onclick = () => {
      offset += pageSize;
      loadVehicles(offset);
    };
  });
})();
