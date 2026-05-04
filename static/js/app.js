document.addEventListener('DOMContentLoaded', () => {
  // ---- MOBILE MENU ----
  const sidebar = document.getElementById('sidebar');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const sidebarOverlay = document.getElementById('sidebar-overlay');

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-active');
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => {
      sidebar.classList.remove('mobile-active');
    });
  }

  // ---- CLOCK ----
  function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2,'0');
    const m = String(now.getMinutes()).padStart(2,'0');
    const el = document.getElementById('sidebar-clock');
    if (el) el.textContent = `${h}:${m}`;
    const d = document.getElementById('sidebar-date');
    if (d) d.textContent = now.toLocaleDateString('es-DO',{weekday:'long',day:'numeric',month:'short'});
  }
  updateClock();
  setInterval(updateClock, 30000);

  // ---- REPORT DATE ----
  const now = new Date();
  const fmt = now.toLocaleDateString('es-DO',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
  const rdl = document.getElementById('report-date-label');
  if (rdl) rdl.textContent = fmt.charAt(0).toUpperCase()+fmt.slice(1);

  // ---- NAVIGATION ----
  const navItems = document.querySelectorAll('.nav-item');
  const views = document.querySelectorAll('.view');
  navItems.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.view;
      navItems.forEach(n => n.classList.remove('active'));
      views.forEach(v => v.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('view-'+target).classList.add('active');
      if (target === 'reports') { loadReports(); loadHistorial('today'); }
      if (target === 'products') loadProductsManagement();
      if (target === 'invoices') loadInvoices('today', 'all');
      
      // Cerrar sidebar en móvil tras navegar
      sidebar.classList.remove('mobile-active');
    });
  });

  // ---- HISTORY TABS (inside table panel) ----
  document.querySelectorAll('#history-tabs .period-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('#history-tabs .period-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadHistorial(tab.dataset.period);
    });
  });

  // ---- EMOJI SELECTOR ----
  let selectedEmoji = '🍕';
  const EMOJI_TO_CAT = {'🍕':'Pizza','🍟':'Papas','🥤':'Bebidas','🥪':'Sandwich','🍗':'Nuggets'};
  document.querySelectorAll('.emoji-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.emoji-opt').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedEmoji = btn.dataset.emoji;
      document.getElementById('product-emoji').value = selectedEmoji;
      // Auto-select matching category
      const catSel = document.getElementById('product-category');
      const matchCat = EMOJI_TO_CAT[selectedEmoji];
      if (catSel && matchCat) catSel.value = matchCat;
    });
  });

  // ---- MODAL PRODUCT ----
  const modal = document.getElementById('product-modal');
  const form = document.getElementById('product-form');
  const modalTitle = document.getElementById('modal-title');
  const modalSubtitle = document.getElementById('modal-subtitle');
  const submitBtn = document.getElementById('modal-submit-btn');

  function openModal(product = null) {
    form.reset();
    document.querySelectorAll('.emoji-opt').forEach(b => b.classList.remove('active'));
    document.querySelector('.emoji-opt[data-emoji="🍕"]').classList.add('active');
    selectedEmoji = '🍕';
    document.getElementById('product-emoji').value = '🍕';
    document.getElementById('edit-product-id').value = '';

    if (product) {
      modalTitle.textContent = 'Editar Producto';
      modalSubtitle.textContent = 'Modifica los datos del producto';
      submitBtn.textContent = 'Guardar Cambios';
      document.getElementById('edit-product-id').value = product.id;
      document.getElementById('product-name').value = product.name;
      document.getElementById('product-price').value = product.price;
      document.getElementById('product-cost').value = product.cost_price || '';
      document.getElementById('product-category').value = product.category || 'General';
      selectedEmoji = product.emoji || '🍕';
      document.getElementById('product-emoji').value = selectedEmoji;
      const emojiBtn = document.querySelector(`.emoji-opt[data-emoji="${selectedEmoji}"]`);
      if (emojiBtn) { document.querySelectorAll('.emoji-opt').forEach(b=>b.classList.remove('active')); emojiBtn.classList.add('active'); }
    } else {
      modalTitle.textContent = 'Nuevo Producto';
      modalSubtitle.textContent = 'Completa los datos del producto';
      submitBtn.textContent = 'Guardar Producto';
    }
    modal.classList.add('active');
    setTimeout(() => document.getElementById('product-name').focus(), 100);
  }

  function closeModal() { modal.classList.remove('active'); form.reset(); }
  document.getElementById('btn-add-product').addEventListener('click', () => openModal());
  document.getElementById('close-modal').addEventListener('click', closeModal);
  document.getElementById('cancel-modal').addEventListener('click', closeModal);
  document.getElementById('modal-backdrop').addEventListener('click', closeModal);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const editId = document.getElementById('edit-product-id').value;
    const name = document.getElementById('product-name').value.trim();
    const price = parseFloat(document.getElementById('product-price').value);
    const cost_price = parseFloat(document.getElementById('product-cost').value) || 0;
    const category = document.getElementById('product-category').value;
    const emoji = document.getElementById('product-emoji').value;
    if (!name || !price) return;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Guardando...';
    try {
      const url = editId ? `/api/products/${editId}` : '/api/products';
      const method = editId ? 'PUT' : 'POST';
      const res = await fetch(url, { method, headers:{'Content-Type':'application/json'}, body: JSON.stringify({name, price, cost_price, category, emoji}) });
      if (res.ok) {
        closeModal();
        showToast(editId ? 'Producto actualizado' : 'Producto agregado');
        loadProducts();
        loadProductsManagement();
      }
    } catch { showToast('Error al guardar', 'error'); }
    finally { submitBtn.disabled = false; submitBtn.textContent = editId ? 'Guardar Cambios' : 'Guardar Producto'; }
  });

  // ---- MODAL CONFIRMAR VENTA ----
  const saleModal = document.getElementById('sale-modal');
  let saleProduct = null;
  let saleQty = 1;

  function openSaleModal(product) {
    saleProduct = product;
    saleQty = 1;
    document.getElementById('sale-modal-emoji').textContent = product.emoji || '🍕';
    document.getElementById('sale-modal-name').textContent = product.name;
    document.getElementById('sale-modal-unit').textContent = `$${product.price.toFixed(2)} / unidad`;
    document.getElementById('sale-qty').textContent = '1';
    document.getElementById('sale-total').textContent = `$${product.price.toFixed(2)}`;
    saleModal.classList.add('active');
  }

  function closeSaleModal() { saleModal.classList.remove('active'); saleProduct = null; }

  function updateSaleQty(delta) {
    saleQty = Math.max(1, saleQty + delta);
    document.getElementById('sale-qty').textContent = saleQty;
    document.getElementById('sale-total').textContent = `$${(saleProduct.price * saleQty).toFixed(2)}`;
  }

  document.getElementById('qty-minus').addEventListener('click', () => updateSaleQty(-1));
  document.getElementById('qty-plus').addEventListener('click', () => updateSaleQty(1));
  document.getElementById('cancel-sale-modal').addEventListener('click', closeSaleModal);
  document.getElementById('sale-modal-backdrop').addEventListener('click', closeSaleModal);
  document.getElementById('confirm-sale-btn').addEventListener('click', async () => {
    if (!saleProduct) return;
    const btn = document.getElementById('confirm-sale-btn');
    btn.disabled = true;
    btn.textContent = 'Registrando...';
    try {
      const res = await fetch('/api/sales', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: saleProduct.id, quantity: saleQty})
      });
      if (res.ok) {
        const saleData = await res.json();
        closeSaleModal();
        showToast(`✓ "${saleData.product_name}" registrado`);
        showInvoiceModal(saleData);
      }
    } catch { showToast('Error al registrar', 'error'); }
    finally { btn.disabled = false; btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Confirmar Venta'; }
  });


  // ---- INVOICE MODAL ----
  let currentSaleId = null;

  function showInvoiceModal(sale) {
    currentSaleId = sale.id;
    const dateObj = new Date(sale.date);
    const dateStr = dateObj.toLocaleDateString('es-DO', {weekday:'long', day:'numeric', month:'long', year:'numeric'});
    const timeStr = dateObj.toLocaleTimeString('es-DO', {hour:'2-digit', minute:'2-digit'});
    document.getElementById('inv-number').textContent = sale.invoice_number || `FAC-${String(sale.id).padStart(4,'0')}`;
    document.getElementById('inv-datetime').textContent = `${dateStr.charAt(0).toUpperCase()+dateStr.slice(1)} · ${timeStr}`;
    document.getElementById('inv-product-name').textContent = `${sale.product_emoji || '🍕'} ${sale.product_name}`;
    document.getElementById('inv-qty').textContent = sale.quantity;
    const unitPrice = sale.unit_price || (sale.price_at_sale / sale.quantity);
    document.getElementById('inv-unit-price').textContent = `$${unitPrice.toFixed(2)}`;
    document.getElementById('inv-item-total').textContent = `$${sale.price_at_sale.toFixed(2)}`;
    document.getElementById('inv-grand-total').textContent = `$${sale.price_at_sale.toFixed(2)}`;
    
    // Datos Internos
    document.getElementById('inv-internal-cost').textContent = `$${(sale.cost_at_sale || 0).toFixed(2)}`;
    document.getElementById('inv-internal-profit').textContent = `$${(sale.profit_at_sale || 0).toFixed(2)}`;
    
    document.getElementById('invoice-modal').classList.add('active');
  }

  function closeInvoiceModal() {
    document.getElementById('invoice-modal').classList.remove('active');
    currentSaleId = null;
  }

  document.getElementById('close-invoice-modal').addEventListener('click', closeInvoiceModal);
  document.getElementById('invoice-modal-backdrop').addEventListener('click', closeInvoiceModal);
  document.getElementById('print-invoice-btn').addEventListener('click', () => window.print());

  document.getElementById('void-invoice-btn').addEventListener('click', async () => {
    if (!currentSaleId) return;
    if (!confirm('¿Seguro que deseas ANULAR esta venta? Esta acción no se puede deshacer.')) return;
    try {
      const res = await fetch(`/api/sales/${currentSaleId}`, { method: 'DELETE' });
      if (res.ok) {
        closeInvoiceModal();
        showToast('Venta anulada', 'error');
        loadReports();
        loadHistorial('today');
      }
    } catch { showToast('Error al anular', 'error'); }
  });


  const deleteModal = document.getElementById('delete-modal');
  let deleteProductId = null;

  function openDeleteModal(id, name) {
    deleteProductId = id;
    document.getElementById('delete-product-name').textContent = name;
    deleteModal.classList.add('active');
  }
  function closeDeleteModal() { deleteModal.classList.remove('active'); deleteProductId = null; }
  document.getElementById('close-delete-modal').addEventListener('click', closeDeleteModal);
  document.getElementById('cancel-delete').addEventListener('click', closeDeleteModal);
  document.getElementById('delete-backdrop').addEventListener('click', closeDeleteModal);
  document.getElementById('confirm-delete').addEventListener('click', async () => {
    if (!deleteProductId) return;
    try {
      const res = await fetch(`/api/products/${deleteProductId}`, {method:'DELETE'});
      if (res.ok) { showToast('Producto eliminado'); closeDeleteModal(); loadProductsManagement(); loadProducts(); }
    } catch { showToast('Error al eliminar','error'); }
  });

  const CAT_NORM = {
    'pizza':'Pizza','pizzas':'Pizza',
    'papas':'Papas','papa':'Papas','fries':'Papas',
    'bebidas':'Bebidas','bebida':'Bebidas','drink':'Bebidas',
    'sandwich':'Sandwich','sandwitch':'Sandwich','sandwiches':'Sandwich',
    'nuggets':'Nuggets','nugget':'Nuggets',
  };
  function normCat(c) {
    const k = (c||'').toLowerCase().trim();
    return CAT_NORM[k] || c || 'Pizza';
  }

  let allPOSProducts = [];
  let activeCat = 'all';

  let activeCategory = 'all';
  let posSearchQuery = '';

  async function loadProducts(cat = 'all', search = '') {
    activeCategory = cat;
    posSearchQuery = search.toLowerCase();
    const grid = document.getElementById('products-grid');
    try {
      const res = await fetch('/api/products');
      let products = await res.json();
      
      if (activeCategory !== 'all') {
        products = products.filter(p => normCat(p.category) === activeCategory);
      }
      
      if (posSearchQuery) {
        products = products.filter(p => p.name.toLowerCase().includes(posSearchQuery));
      }

      if (!products.length) {
        grid.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><p class="empty-title">Sin resultados</p><p class="empty-sub">No se encontró "${search}"</p></div>`;
        return;
      }
      
      grid.innerHTML = '';
      products.forEach(p => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
          <div class="product-emoji">${p.emoji||'🍕'}</div>
          <div class="product-name">${p.name}</div>
          <div class="product-price-badge">$${p.price.toFixed(2)}</div>
        `;
        card.addEventListener('click', (e) => {
          const rect = card.getBoundingClientRect();
          const ripple = document.createElement('div');
          ripple.className = 'ripple-effect';
          ripple.style.left = (e.clientX - rect.left - 40) + 'px';
          ripple.style.top  = (e.clientY - rect.top  - 40) + 'px';
          card.appendChild(ripple);
          setTimeout(() => ripple.remove(), 700);
          openSaleModal(p);
        });
        grid.appendChild(card);
      });
    } catch { grid.innerHTML = '<p style="color:#EF4444;padding:20px">Error al cargar productos</p>'; }
  }
  loadProducts();

  // Search POS
  const posSearchInput = document.getElementById('pos-search-input');
  if (posSearchInput) {
    posSearchInput.addEventListener('input', (e) => {
      loadProducts(activeCategory, e.target.value);
    });
  }

  document.querySelectorAll('#cat-tabs .cat-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('#cat-tabs .cat-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadProducts(tab.dataset.cat, posSearchInput.value);
    });
  });

  async function loadStats() {
    try {
      const res = await fetch('/api/stats');
      await res.json(); // keep alive for init
    } catch {}
  }

  // ---- REPORTS ----
  async function loadReports() {
    try {
      const res = await fetch('/api/stats');
      const stats = await res.json();

      // HOY
      const todayStr = new Date().toLocaleDateString('es-DO',{weekday:'long', day:'numeric', month:'long'});
      const totalEl = document.getElementById('report-total');
      const profitEl = document.getElementById('report-profit');
      const countEl = document.getElementById('report-count');
      if (totalEl) totalEl.textContent = '$' + (stats.daily_revenue || 0).toFixed(2);
      if (profitEl) profitEl.textContent = '$' + (stats.daily_profit || 0).toFixed(2);
      if (countEl) countEl.textContent = stats.daily_count || 0;

      // Mostrar fecha de hoy en la tarjeta
      const delta = document.getElementById('report-delta');
      if (delta) delta.textContent = todayStr.charAt(0).toUpperCase() + todayStr.slice(1);
    } catch(err) { console.error(err); }
  }

  async function loadHistorial(period) {
    try {
      const res = await fetch(`/api/sales/history?period=${period}`);
      const sales = await res.json();

      // Update column header label
      const th = document.getElementById('th-fecha');
      if (th) th.textContent = period === 'today' ? 'Hora' : 'Fecha';

      const badge = document.getElementById('sales-count-badge');
      const total = sales.reduce((s, v) => s + v.price_at_sale, 0);
      if (badge) badge.textContent = `${sales.length} ventas · $${total.toFixed(2)}`;

      const tbody = document.getElementById('sales-table-body');
      if (!sales.length) {
        const labels = {today:'hoy', week:'esta semana', month:'este mes'};
        tbody.innerHTML = `<tr><td colspan="5" class="empty-row">No hay ventas registradas ${labels[period]||''}.</td></tr>`;
        return;
      }
      tbody.innerHTML = '';
      sales.forEach((s,i) => {
        const dateObj = new Date(s.date);
        const timeLabel = period === 'today'
          ? dateObj.toLocaleTimeString('es-DO',{hour:'2-digit',minute:'2-digit'})
          : dateObj.toLocaleDateString('es-DO',{weekday:'short',day:'numeric',month:'short'});
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td data-label="#">#${sales.length-i}</td>
          <td data-label="Producto"><div class="sale-product"><span class="sale-product-emoji">${s.product_emoji||'🍕'}</span>${s.product_name}</div></td>
          <td data-label="${period === 'today' ? 'Hora' : 'Fecha'}" class="table-time">${timeLabel}</td>
          <td data-label="Cant.">${s.quantity}</td>
          <td data-label="Total" class="table-amount">$${s.price_at_sale.toFixed(2)}</td>`;
        tbody.appendChild(tr);
      });
    } catch(err) { console.error(err); }
  }

  // ---- PRODUCTS MANAGEMENT ----
  async function loadProductsManagement() {
    const list = document.getElementById('products-management-list');
    try {
      const res = await fetch('/api/products');
      const products = await res.json();
      if (!products.length) {
        list.innerHTML = '<div class="empty-state" style="grid-column:1/-1"><div class="empty-icon">📋</div><p class="empty-title">Sin productos</p><p class="empty-sub">Agrega el primer producto</p></div>';
        return;
      }
      list.innerHTML = '';
      products.forEach(p => {
        const card = document.createElement('div');
        card.className = 'product-mgmt-card';
        card.innerHTML = `
          <div class="mgmt-emoji-box">${p.emoji||'🍕'}</div>
          <div class="mgmt-details">
            <div class="mgmt-name">${p.name}</div>
            <div class="mgmt-category">${p.category||'General'}</div>
            <div class="mgmt-prices">
              <div class="mgmt-price-item">
                <span class="price-dot sale"></span>
                <span class="price-lab">Venta:</span>
                <span class="price-val">$${p.price.toFixed(2)}</span>
              </div>
              <div class="mgmt-price-item">
                <span class="price-dot cost"></span>
                <span class="price-lab">Costo:</span>
                <span class="price-val">$${(p.cost_price||0).toFixed(2)}</span>
              </div>
            </div>
          </div>
          <div class="mgmt-actions">
            <button class="btn-icon btn-edit" title="Editar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="btn-icon btn-delete" title="Eliminar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/></svg>
            </button>
          </div>`;
        card.querySelector('.btn-edit').addEventListener('click', () => openModal(p));
        card.querySelector('.btn-delete').addEventListener('click', () => openDeleteModal(p.id, p.name));
        list.appendChild(card);
      });
    } catch { list.innerHTML = '<p style="color:#EF4444;padding:20px">Error al cargar</p>'; }
  }

  // ---- TOAST ----
  function showToast(msg, type='success') {
    const t = document.getElementById('toast');
    const icon = document.getElementById('toast-icon');
    const m = document.getElementById('toast-msg');
    m.textContent = msg;
    icon.style.background = type==='error' ? '#EF4444' : 'var(--green)';
    icon.textContent = type==='error' ? '✕' : '✓';
    t.classList.add('show');
    clearTimeout(t._t);
    t._t = setTimeout(() => t.classList.remove('show'), 3000);
  }

  // ---- INVOICES VIEW ----
  let invActivePeriod = 'today';
  let invActiveProduct = 'all';

  async function loadInvoices(period, productId) {
    invActivePeriod = period;
    invActiveProduct = productId;

    // Load product chips on first load
    const chipsWrap = document.getElementById('inv-product-chips');
    if (chipsWrap && chipsWrap.children.length <= 1) {
      try {
        const res = await fetch('/api/products');
        const products = await res.json();
        products.forEach(p => {
          const btn = document.createElement('button');
          btn.className = 'inv-chip';
          btn.dataset.productId = p.id;
          btn.innerHTML = `<span class="chip-emoji">${p.emoji}</span> ${p.name}`;
          btn.addEventListener('click', () => {
            document.querySelectorAll('.inv-chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            loadInvoices(invActivePeriod, String(p.id));
          });
          chipsWrap.appendChild(btn);
        });
      } catch {}
    }

    try {
      const url = `/api/sales/history?period=${period}&product_id=${productId}`;
      const res = await fetch(url);
      let sales = await res.json();

      // Aplicar búsqueda local si hay texto
      const search = document.getElementById('inv-search-input').value.trim().toUpperCase();
      if (search) {
        sales = sales.filter(s => {
          const invNum = (s.invoice_number || `FAC-${String(s.id).padStart(4,'0')}`).toUpperCase();
          return invNum.includes(search);
        });
      }

      // Update stats bar
      const total = sales.reduce((s, v) => s + v.price_at_sale, 0);
      document.getElementById('inv-count-label').textContent = sales.length;
      document.getElementById('inv-total-label').textContent = `$${total.toFixed(2)}`;

      const tbody = document.getElementById('invoices-table-body');
      if (!sales.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-row">No hay facturas para este período.</td></tr>';
        return;
      }
      tbody.innerHTML = '';
      sales.forEach(s => {
        const dateObj = new Date(s.date);
        const isPeriodToday = invActivePeriod === 'today';
        const timeLabel = isPeriodToday
          ? dateObj.toLocaleTimeString('es-DO', {hour:'2-digit', minute:'2-digit'})
          : dateObj.toLocaleDateString('es-DO', {weekday:'short', day:'numeric', month:'short'});
        const unitPrice = s.unit_price || (s.price_at_sale / s.quantity);
        const invNum = s.invoice_number || `FAC-${String(s.id).padStart(4,'0')}`;
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td data-label="Factura"><span class="inv-num-badge">${invNum}</span></td>
          <td data-label="Producto"><div class="sale-product"><span class="sale-product-emoji">${s.product_emoji||'🍕'}</span>${s.product_name}</div></td>
          <td data-label="Fecha" class="table-time">${timeLabel}</td>
          <td data-label="Cantidad">${s.quantity}</td>
          <td data-label="P/U">$${unitPrice.toFixed(2)}</td>
          <td data-label="Total" class="table-amount">$${s.price_at_sale.toFixed(2)}</td>
          <td class="table-actions">
            <button class="btn-reprint" title="Reimprimir"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg> <span>Imprimir</span></button>
            <button class="btn-void-sale" title="Anular"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/></svg> <span>Anular</span></button>
          </td>`;
        tr.querySelector('.btn-reprint').addEventListener('click', () => showInvoiceModal(s));
        tr.querySelector('.btn-void-sale').addEventListener('click', async () => {
          if (!confirm(`¿Anular la factura ${invNum}? Esta acción no se puede deshacer.`)) return;
          try {
            const res = await fetch(`/api/sales/${s.id}`, { method: 'DELETE' });
            if (res.ok) {
              showToast('Venta anulada', 'error');
              loadInvoices(invActivePeriod, invActiveProduct);
              loadReports();
            }
          } catch { showToast('Error al anular', 'error'); }
        });
        tbody.appendChild(tr);
      });
    } catch(err) { console.error(err); }
  }

  // Eventos de filtros de facturas
  document.querySelectorAll('#inv-period-tabs .period-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('#inv-period-tabs .period-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      loadInvoices(tab.dataset.period, invActiveProduct);
    });
  });

  const invSearch = document.getElementById('inv-search-input');
  if (invSearch) {
    invSearch.addEventListener('input', () => {
      loadInvoices(invActivePeriod, invActiveProduct);
    });
  }

  // "Todos" chip
  document.querySelector('.inv-chip[data-product-id="all"]').addEventListener('click', () => {
    document.querySelectorAll('.inv-chip').forEach(c => c.classList.remove('active'));
    document.querySelector('.inv-chip[data-product-id="all"]').classList.add('active');
    loadInvoices(invActivePeriod, 'all');
  });

  // ---- INIT ----
  loadProducts();
  loadReports();
  loadHistorial('today');
});
