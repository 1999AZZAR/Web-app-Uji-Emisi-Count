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
    clearBtn.classList.add('hidden');
    clearBtn.onclick = () => {
      document.getElementById('confirmText').textContent = `Hapus data uji ${plat}?`;
      confirmModal.classList.remove('hidden');
      document.getElementById('confirmYes').onclick = async () => {
        const res = await fetch(`/api/hasil-uji/${plat}`, { method: 'DELETE' });
        if (res.ok) {
          showToast('Data uji dihapus', 'success'); fetchTestedPlats().then(() => loadVehicles(offset)); modal.classList.add('hidden');
        } else showToast('Gagal menghapus data uji', 'error');
        confirmModal.classList.add('hidden');
      };
    };
    modal.classList.remove('hidden');
    document.getElementById('kendaraan_detail').textContent = plat;
    const info = document.getElementById('kendaraan_info');
    info.style.display = 'block';
    const form = document.getElementById('hasilUjiForm');
    form.style.display = 'block';
    document.getElementById('hasil').classList.add('hidden');
    const res = await fetch(`/api/hasil-uji/${plat}`);
    if (res.ok) {
      const data = await res.json();
      ['co','co2','hc','o2','lambda'].forEach(id => {
        document.getElementById(id).value = data[id] || '';
      });
      document.getElementById('hasil').classList.remove('hidden');
      clearBtn.classList.remove('hidden');
    } else {
      form.reset();
      clearBtn.classList.add('hidden');
    }
    form.onsubmit = async e => {
      e.preventDefault();
      const payload = {
        co: parseFloat(document.getElementById('co').value),
        co2: parseFloat(document.getElementById('co2').value),
        hc: parseFloat(document.getElementById('hc').value),
        o2: parseFloat(document.getElementById('o2').value),
        lambda_val: parseFloat(document.getElementById('lambda').value),
        user_id: parseInt(document.getElementById('currentUserId').value)
      };
      const rsp = await fetch(`/api/hasil-uji/${plat}`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if (rsp.ok) {
        const result = await rsp.json();
        showToast(`Tersimpan – Valid: ${result.valid}, Lulus: ${result.lulus}, Operator: ${result.operator}`, 'success');
        fetchTestedPlats().then(() => loadVehicles(offset)); modal.classList.add('hidden');
      } else {
        const error = await rsp.json();
        showToast(`Gagal menyimpan data: ${error.message}`, 'error');
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
