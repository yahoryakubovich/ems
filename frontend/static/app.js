'use strict';

// ─── CONSTANTS ───────────────────────────────────────────────────────────────

const STATUS_LABELS = {
  in_stock: 'In Stock',
  assigned: 'Assigned',
  maintenance: 'Maintenance',
  retired: 'Retired',
};

const MOVEMENT_LABELS = {
  assign: 'Assigned',
  transfer: 'Transferred',
  unassign: 'Returned',
};

const PAGE_SIZE = 25;

// ─── STATE ───────────────────────────────────────────────────────────────────

const state = {
  tab: 'equipment',
  categories: [],
  equipment: { items: [], total: 0 },
  stats: { total: 0, in_stock: 0, assigned: 0, maintenance: 0, retired: 0 },
  filters: { search: '', status: '', category_id: '', skip: 0, limit: PAGE_SIZE },
  loading: false,
};

// ─── API ─────────────────────────────────────────────────────────────────────

async function req(path, { method = 'GET', body } = {}) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

function qs(params) {
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  );
  return new URLSearchParams(clean).toString();
}

const api = {
  categories: {
    list:   ()       => req('/categories/?limit=200'),
    create: (d)      => req('/categories/', { method: 'POST', body: d }),
    update: (id, d)  => req(`/categories/${id}`, { method: 'PUT', body: d }),
    delete: (id)     => req(`/categories/${id}`, { method: 'DELETE' }),
  },
  equipment: {
    list:     (p)    => req(`/equipment/?${qs(p)}`),
    create:   (d)    => req('/equipment/', { method: 'POST', body: d }),
    update:   (id,d) => req(`/equipment/${id}`, { method: 'PUT', body: d }),
    delete:   (id)   => req(`/equipment/${id}`, { method: 'DELETE' }),
    assign:   (id,d) => req(`/equipment/${id}/assign`, { method: 'POST', body: d }),
    transfer: (id,d) => req(`/equipment/${id}/transfer`, { method: 'POST', body: d }),
    unassign: (id,d) => req(`/equipment/${id}/unassign`, { method: 'POST', body: d }),
    history:  (id)   => req(`/equipment/${id}/history`),
  },
};

// ─── HELPERS ─────────────────────────────────────────────────────────────────

const h = (s) => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

function badge(status) {
  return `<span class="badge badge-${h(status)}">${h(STATUS_LABELS[status] ?? status)}</span>`;
}

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric' });
}

function fmtDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', { year:'numeric', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' });
}

function catName(id) {
  return state.categories.find(c => c.id === id)?.name ?? String(id);
}

let _toastTimer = null;
function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type ? 't-' + type : ''}`;
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.add('hidden'), 3000);
}

function icon(path, size = 15) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
}

const ICONS = {
  search:   '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>',
  plus:     '<path d="M12 5v14M5 12h14"/>',
  edit:     '<path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>',
  trash:    '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>',
  assign:   '<path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6M22 11h-6"/>',
  unassign: '<path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 11H16"/>',
  transfer: '<path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 3 22 9 16 15"/>',
  history:  '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  close:    '<path d="M18 6L6 18M6 6l12 12"/>',
  chevL:    '<polyline points="15 18 9 12 15 6"/>',
  chevR:    '<polyline points="9 18 15 12 9 6"/>',
};

// ─── DATA LOADING ─────────────────────────────────────────────────────────────

async function loadCategories() {
  const data = await api.categories.list();
  state.categories = data.items ?? [];
}

async function loadStats() {
  const [all, s1, s2, s3, s4] = await Promise.all([
    api.equipment.list({ limit: 1, skip: 0 }),
    api.equipment.list({ limit: 1, skip: 0, status: 'in_stock' }),
    api.equipment.list({ limit: 1, skip: 0, status: 'assigned' }),
    api.equipment.list({ limit: 1, skip: 0, status: 'maintenance' }),
    api.equipment.list({ limit: 1, skip: 0, status: 'retired' }),
  ]);
  state.stats = {
    total: all.total,
    in_stock: s1.total,
    assigned: s2.total,
    maintenance: s3.total,
    retired: s4.total,
  };
}

async function loadEquipment() {
  state.loading = true;
  renderMain();
  const params = { ...state.filters };
  if (!params.search) delete params.search;
  if (!params.status) delete params.status;
  if (!params.category_id) delete params.category_id;
  const data = await api.equipment.list(params);
  state.equipment = { items: data.items ?? [], total: data.total ?? 0 };
  state.loading = false;
  renderMain();
}

// ─── RENDER ───────────────────────────────────────────────────────────────────

function renderMain() {
  const el = document.getElementById('main');
  el.innerHTML = state.tab === 'equipment' ? renderEquipmentView() : renderCategoriesView();
  attachListeners();
}

function renderEquipmentView() {
  return `
    ${renderStats()}
    <div class="toolbar">
      <div class="search-wrap">
        ${icon(ICONS.search, 14)}
        <input type="text" id="search-input" placeholder="Search by name or inventory #…"
          value="${h(state.filters.search)}">
      </div>
      <select class="filter-sel" id="status-filter">
        <option value="">All statuses</option>
        ${Object.entries(STATUS_LABELS).map(([v, l]) =>
          `<option value="${v}" ${state.filters.status === v ? 'selected' : ''}>${h(l)}</option>`
        ).join('')}
      </select>
      <select class="filter-sel" id="category-filter">
        <option value="">All categories</option>
        ${state.categories.map(c =>
          `<option value="${c.id}" ${state.filters.category_id == c.id ? 'selected' : ''}>${h(c.name)}</option>`
        ).join('')}
      </select>
      <button class="btn btn-primary" id="btn-add-equipment">
        ${icon(ICONS.plus, 14)} Add Equipment
      </button>
    </div>
    <div class="table-card">
      ${state.loading ? renderLoading() : renderEquipmentTable()}
    </div>
  `;
}

function renderStats() {
  const s = state.stats;
  return `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total</div>
        <div class="stat-value">${s.total}</div>
      </div>
      <div class="stat-card s-green">
        <div class="stat-label">In Stock</div>
        <div class="stat-value">${s.in_stock}</div>
      </div>
      <div class="stat-card s-blue">
        <div class="stat-label">Assigned</div>
        <div class="stat-value">${s.assigned}</div>
      </div>
      <div class="stat-card s-amber">
        <div class="stat-label">Maintenance</div>
        <div class="stat-value">${s.maintenance}</div>
      </div>
      <div class="stat-card s-red">
        <div class="stat-label">Retired</div>
        <div class="stat-value">${s.retired}</div>
      </div>
    </div>
  `;
}

function renderLoading() {
  return `<div class="loading-wrap"><div class="spinner"></div> Loading…</div>`;
}

function renderEquipmentTable() {
  const items = state.equipment.items;
  if (!items.length) {
    return `<table class="data-table"><tbody><tr><td class="table-empty">No equipment found.</td></tr></tbody></table>`;
  }
  const rows = items.map(eq => {
    const isAssigned   = eq.status === 'assigned';
    const canAssign    = ['in_stock'].includes(eq.status);
    const canTransfer  = isAssigned;
    const canUnassign  = isAssigned;
    const canDelete    = !isAssigned;
    const cost = eq.purchase_cost
      ? `${parseFloat(eq.purchase_cost.amount).toLocaleString('en-US', { style:'currency', currency: eq.purchase_cost.currency })}`
      : '—';
    return `
      <tr>
        <td style="color:var(--text-muted);font-size:0.72rem">${eq.id}</td>
        <td><code style="font-size:0.75rem;background:var(--bg);padding:2px 6px;border-radius:4px">${h(eq.inventory_number)}</code></td>
        <td style="font-weight:500">${h(eq.name)}</td>
        <td>${h(catName(eq.category_id))}</td>
        <td>${badge(eq.status)}</td>
        <td style="color:var(--text-muted)">${eq.assigned_to_employee_id ? `#${eq.assigned_to_employee_id}` : '—'}</td>
        <td style="color:var(--text-muted)">${cost}</td>
        <td>
          <div class="actions">
            <button class="action-btn info" title="History" data-action="history" data-id="${eq.id}">
              ${icon(ICONS.history, 14)}
            </button>
            <button class="action-btn" title="Edit" data-action="edit-equipment" data-id="${eq.id}">
              ${icon(ICONS.edit, 14)}
            </button>
            <button class="action-btn success" title="Assign" data-action="assign" data-id="${eq.id}"
              ${canAssign ? '' : 'disabled'}>
              ${icon(ICONS.assign, 14)}
            </button>
            <button class="action-btn" title="Transfer" data-action="transfer" data-id="${eq.id}"
              ${canTransfer ? '' : 'disabled'}>
              ${icon(ICONS.transfer, 14)}
            </button>
            <button class="action-btn" title="Unassign" data-action="unassign" data-id="${eq.id}"
              ${canUnassign ? '' : 'disabled'}>
              ${icon(ICONS.unassign, 14)}
            </button>
            <button class="action-btn danger" title="Delete" data-action="delete-equipment" data-id="${eq.id}"
              ${canDelete ? '' : 'disabled'}>
              ${icon(ICONS.trash, 14)}
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  const skip = state.filters.skip;
  const total = state.equipment.total;
  const limit = state.filters.limit;
  const page = Math.floor(skip / limit) + 1;
  const pages = Math.ceil(total / limit);

  return `
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th><th>Inv #</th><th>Name</th><th>Category</th>
          <th>Status</th><th>Employee</th><th>Cost</th><th>Actions</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
    <div class="pagination">
      <span>${skip + 1}–${Math.min(skip + limit, total)} of ${total}</span>
      <div class="pagination-btns">
        <button class="btn btn-secondary btn-sm" id="page-prev" ${page <= 1 ? 'disabled' : ''}>
          ${icon(ICONS.chevL, 12)}
        </button>
        <button class="btn btn-secondary btn-sm" id="page-next" ${page >= pages ? 'disabled' : ''}>
          ${icon(ICONS.chevR, 12)}
        </button>
      </div>
    </div>
  `;
}

function renderCategoriesView() {
  const cards = state.categories.length
    ? state.categories.map(c => `
        <div class="category-card">
          <div class="cat-name">${h(c.name)}</div>
          <div class="cat-desc">${h(c.description ?? '')}</div>
          <div class="cat-actions">
            <button class="btn btn-secondary btn-sm" data-action="edit-category" data-id="${c.id}">
              ${icon(ICONS.edit, 12)} Edit
            </button>
            <button class="btn btn-danger btn-sm" data-action="delete-category" data-id="${c.id}">
              ${icon(ICONS.trash, 12)} Delete
            </button>
          </div>
        </div>
      `).join('')
    : `<p style="color:var(--text-muted);font-size:0.875rem">No categories yet.</p>`;

  return `
    <div class="section-header">
      <h2 class="section-title">Categories</h2>
      <button class="btn btn-primary" id="btn-add-category">
        ${icon(ICONS.plus, 14)} Add Category
      </button>
    </div>
    <div class="category-grid">${cards}</div>
  `;
}

// ─── MODALS ───────────────────────────────────────────────────────────────────

function openModal(title, bodyHtml, footerHtml) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHtml;
  document.getElementById('modal-footer').innerHTML = footerHtml;
  document.getElementById('modal-backdrop').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-backdrop').classList.add('hidden');
}

function modalEquipmentForm(eq = null) {
  const isEdit = eq !== null;
  const catOptions = state.categories.map(c =>
    `<option value="${c.id}" ${isEdit && eq.category_id === c.id ? 'selected' : ''}>${h(c.name)}</option>`
  ).join('');
  const statusOptions = ['in_stock', 'maintenance', 'retired'].map(s =>
    `<option value="${s}" ${isEdit && eq.status === s ? 'selected' : ''}>${h(STATUS_LABELS[s])}</option>`
  ).join('');

  const body = `
    <div class="form-grid">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Inventory Number *</label>
          <input class="form-input" id="f-inv" value="${h(eq?.inventory_number ?? '')}"
            ${isEdit ? 'disabled' : ''} placeholder="e.g. LT-001">
        </div>
        <div class="form-group">
          <label class="form-label">Name *</label>
          <input class="form-input" id="f-name" value="${h(eq?.name ?? '')}" placeholder="e.g. MacBook Pro 14">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Category *</label>
          <select class="form-select" id="f-cat">
            <option value="">Select…</option>${catOptions}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Status</label>
          <select class="form-select" id="f-status">${statusOptions}</select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Serial Number</label>
          <input class="form-input" id="f-serial" value="${h(eq?.serial_number ?? '')}" placeholder="Optional">
        </div>
        <div class="form-group">
          <label class="form-label">Purchase Date</label>
          <input class="form-input" type="date" id="f-date" value="${h(eq?.purchase_date ?? '')}">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Cost Amount</label>
          <input class="form-input" type="number" step="0.01" min="0" id="f-amount"
            value="${eq?.purchase_cost?.amount ?? ''}" placeholder="0.00">
        </div>
        <div class="form-group">
          <label class="form-label">Currency</label>
          <input class="form-input" id="f-currency" maxlength="3"
            value="${h(eq?.purchase_cost?.currency ?? 'USD')}" placeholder="USD">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Notes</label>
        <textarea class="form-textarea" id="f-notes">${h(eq?.notes ?? '')}</textarea>
      </div>
    </div>
  `;
  const footer = `
    <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
    <button class="btn btn-primary" id="modal-save" data-edit-id="${isEdit ? eq.id : ''}">
      ${isEdit ? 'Save Changes' : 'Create Equipment'}
    </button>
  `;
  openModal(isEdit ? 'Edit Equipment' : 'New Equipment', body, footer);
}

function modalCategoryForm(cat = null) {
  const isEdit = cat !== null;
  const body = `
    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Name *</label>
        <input class="form-input" id="fc-name" value="${h(cat?.name ?? '')}" placeholder="e.g. Laptops">
      </div>
      <div class="form-group">
        <label class="form-label">Description</label>
        <textarea class="form-textarea" id="fc-desc">${h(cat?.description ?? '')}</textarea>
      </div>
    </div>
  `;
  const footer = `
    <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
    <button class="btn btn-primary" id="modal-save-cat" data-edit-id="${isEdit ? cat.id : ''}">
      ${isEdit ? 'Save Changes' : 'Create Category'}
    </button>
  `;
  openModal(isEdit ? 'Edit Category' : 'New Category', body, footer);
}

function modalAssign(equipmentId) {
  const body = `
    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Employee ID *</label>
        <input class="form-input" type="number" min="1" id="f-emp" placeholder="e.g. 101">
      </div>
      <div class="form-group">
        <label class="form-label">Comment</label>
        <input class="form-input" id="f-comment" placeholder="Optional">
      </div>
    </div>
  `;
  const footer = `
    <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
    <button class="btn btn-primary" id="modal-do-assign" data-id="${equipmentId}">Assign</button>
  `;
  openModal('Assign Equipment', body, footer);
}

function modalTransfer(equipmentId) {
  const body = `
    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Transfer to Employee ID *</label>
        <input class="form-input" type="number" min="1" id="f-to-emp" placeholder="e.g. 202">
      </div>
      <div class="form-group">
        <label class="form-label">Comment</label>
        <input class="form-input" id="f-comment" placeholder="Optional">
      </div>
    </div>
  `;
  const footer = `
    <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
    <button class="btn btn-primary" id="modal-do-transfer" data-id="${equipmentId}">Transfer</button>
  `;
  openModal('Transfer Equipment', body, footer);
}

function modalUnassign(equipmentId) {
  const body = `
    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Comment</label>
        <input class="form-input" id="f-comment" placeholder="Optional reason">
      </div>
    </div>
  `;
  const footer = `
    <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
    <button class="btn btn-danger" id="modal-do-unassign" data-id="${equipmentId}">Unassign</button>
  `;
  openModal('Unassign Equipment', body, footer);
}

function modalHistory(equipmentId, movements) {
  const body = movements.length === 0
    ? `<div class="history-empty">No movement history yet.</div>`
    : `<div class="timeline">${movements.map(m => {
        const dotCls = `dot-${m.movement_type}`;
        const label = MOVEMENT_LABELS[m.movement_type] ?? m.movement_type;
        let detail = '';
        if (m.movement_type === 'assign')    detail = `To employee #${m.to_employee_id}`;
        if (m.movement_type === 'transfer')  detail = `From #${m.from_employee_id} → #${m.to_employee_id}`;
        if (m.movement_type === 'unassign')  detail = `From employee #${m.from_employee_id}`;
        return `
          <div class="timeline-item">
            <div class="timeline-dot ${dotCls}">${label.slice(0,3)}</div>
            <div class="timeline-content">
              <div class="tl-type">${h(label)}</div>
              <div class="tl-detail">${h(detail)}${m.comment ? ` — ${h(m.comment)}` : ''}</div>
              <div class="tl-time">${fmtDateTime(m.happened_at)}</div>
            </div>
          </div>
        `;
      }).join('')}</div>`;
  openModal(`Movement History — Equipment #${equipmentId}`, body,
    `<button class="btn btn-secondary" id="modal-cancel">Close</button>`);
}

function modalConfirmDelete(type, id, name) {
  const body = `<p>Delete <strong>${h(name)}</strong>? This cannot be undone.</p>`;
  const footer = `
    <button class="btn btn-secondary" id="modal-cancel">Cancel</button>
    <button class="btn btn-danger" id="modal-confirm-delete" data-type="${type}" data-id="${id}">Delete</button>
  `;
  openModal('Confirm Delete', body, footer);
}

// ─── EVENT LISTENERS ──────────────────────────────────────────────────────────

function attachListeners() {
  // Tab switching
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.tab = btn.dataset.tab;
      renderMain();
    });
  });

  // Search (debounced)
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    let debounce;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        state.filters.search = searchInput.value;
        state.filters.skip = 0;
        loadEquipment();
      }, 350);
    });
  }

  // Status filter
  const statusSel = document.getElementById('status-filter');
  if (statusSel) {
    statusSel.addEventListener('change', () => {
      state.filters.status = statusSel.value;
      state.filters.skip = 0;
      loadEquipment();
    });
  }

  // Category filter
  const catSel = document.getElementById('category-filter');
  if (catSel) {
    catSel.addEventListener('change', () => {
      state.filters.category_id = catSel.value;
      state.filters.skip = 0;
      loadEquipment();
    });
  }

  // Pagination
  document.getElementById('page-prev')?.addEventListener('click', () => {
    state.filters.skip = Math.max(0, state.filters.skip - state.filters.limit);
    loadEquipment();
  });
  document.getElementById('page-next')?.addEventListener('click', () => {
    state.filters.skip += state.filters.limit;
    loadEquipment();
  });

  // Add equipment button
  document.getElementById('btn-add-equipment')?.addEventListener('click', () => {
    modalEquipmentForm();
  });

  // Add category button
  document.getElementById('btn-add-category')?.addEventListener('click', () => {
    modalCategoryForm();
  });

  // Row action buttons (event delegation on main)
  document.getElementById('main').addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.dataset.action;
    const id = parseInt(btn.dataset.id, 10);
    const eq = state.equipment.items.find(x => x.id === id);

    if (action === 'history') {
      const data = await api.equipment.history(id).catch(err => { toast(err.message, 'error'); return null; });
      if (data) modalHistory(id, data.movements);
    }
    if (action === 'edit-equipment' && eq) modalEquipmentForm(eq);
    if (action === 'assign')   modalAssign(id);
    if (action === 'transfer') modalTransfer(id);
    if (action === 'unassign') modalUnassign(id);
    if (action === 'delete-equipment' && eq) {
      modalConfirmDelete('equipment', id, eq.name);
    }
    if (action === 'edit-category') {
      const cat = state.categories.find(c => c.id === id);
      if (cat) modalCategoryForm(cat);
    }
    if (action === 'delete-category') {
      const cat = state.categories.find(c => c.id === id);
      if (cat) modalConfirmDelete('category', id, cat.name);
    }
  });

  // Modal close
  document.getElementById('modal-close')?.addEventListener('click', closeModal);
  document.getElementById('modal-backdrop')?.addEventListener('click', (e) => {
    if (e.target.id === 'modal-backdrop') closeModal();
  });
}

function attachModalListeners() {
  document.getElementById('modal-cancel')?.addEventListener('click', closeModal);

  // Save equipment (create or edit)
  document.getElementById('modal-save')?.addEventListener('click', async (btn) => {
    const editId = btn.currentTarget.dataset.editId;
    const invNum = document.getElementById('f-inv')?.value?.trim();
    const name   = document.getElementById('f-name')?.value?.trim();
    const catId  = parseInt(document.getElementById('f-cat')?.value, 10);
    const status = document.getElementById('f-status')?.value;
    const serial = document.getElementById('f-serial')?.value?.trim() || null;
    const date   = document.getElementById('f-date')?.value || null;
    const amount = parseFloat(document.getElementById('f-amount')?.value);
    const curr   = document.getElementById('f-currency')?.value?.trim() || null;
    const notes  = document.getElementById('f-notes')?.value?.trim() || null;

    if (!name || (!editId && !invNum) || !catId) {
      toast('Inventory #, Name and Category are required', 'error'); return;
    }

    try {
      if (editId) {
        const payload = { name, category_id: catId, status, serial_number: serial,
          purchase_date: date, notes,
          ...(isNaN(amount) ? { purchase_cost_amount: null } : { purchase_cost_amount: amount, purchase_cost_currency: curr }) };
        await api.equipment.update(parseInt(editId, 10), payload);
        toast('Equipment updated', 'success');
      } else {
        const payload = { inventory_number: invNum, name, category_id: catId, status, serial_number: serial,
          purchase_date: date, notes,
          ...(isNaN(amount) ? {} : { purchase_cost_amount: amount, purchase_cost_currency: curr }) };
        await api.equipment.create(payload);
        toast('Equipment created', 'success');
      }
      closeModal();
      await Promise.all([loadStats(), loadEquipment()]);
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  // Save category
  document.getElementById('modal-save-cat')?.addEventListener('click', async (e) => {
    const editId = e.currentTarget.dataset.editId;
    const name = document.getElementById('fc-name')?.value?.trim();
    const desc = document.getElementById('fc-desc')?.value?.trim() || null;
    if (!name) { toast('Name is required', 'error'); return; }
    try {
      if (editId) {
        await api.categories.update(parseInt(editId, 10), { name, description: desc });
        toast('Category updated', 'success');
      } else {
        await api.categories.create({ name, description: desc });
        toast('Category created', 'success');
      }
      closeModal();
      await loadCategories();
      renderMain();
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  // Assign
  document.getElementById('modal-do-assign')?.addEventListener('click', async (e) => {
    const id = parseInt(e.currentTarget.dataset.id, 10);
    const empId = parseInt(document.getElementById('f-emp')?.value, 10);
    const comment = document.getElementById('f-comment')?.value?.trim() || null;
    if (!empId || empId <= 0) { toast('Employee ID is required', 'error'); return; }
    try {
      await api.equipment.assign(id, { employee_id: empId, comment });
      toast('Equipment assigned', 'success');
      closeModal();
      await Promise.all([loadStats(), loadEquipment()]);
    } catch (err) { toast(err.message, 'error'); }
  });

  // Transfer
  document.getElementById('modal-do-transfer')?.addEventListener('click', async (e) => {
    const id = parseInt(e.currentTarget.dataset.id, 10);
    const toEmp = parseInt(document.getElementById('f-to-emp')?.value, 10);
    const comment = document.getElementById('f-comment')?.value?.trim() || null;
    if (!toEmp || toEmp <= 0) { toast('Target employee ID is required', 'error'); return; }
    try {
      await api.equipment.transfer(id, { to_employee_id: toEmp, comment });
      toast('Equipment transferred', 'success');
      closeModal();
      await Promise.all([loadStats(), loadEquipment()]);
    } catch (err) { toast(err.message, 'error'); }
  });

  // Unassign
  document.getElementById('modal-do-unassign')?.addEventListener('click', async (e) => {
    const id = parseInt(e.currentTarget.dataset.id, 10);
    const comment = document.getElementById('f-comment')?.value?.trim() || null;
    try {
      await api.equipment.unassign(id, { comment });
      toast('Equipment unassigned', 'success');
      closeModal();
      await Promise.all([loadStats(), loadEquipment()]);
    } catch (err) { toast(err.message, 'error'); }
  });

  // Confirm delete
  document.getElementById('modal-confirm-delete')?.addEventListener('click', async (e) => {
    const { type, id } = e.currentTarget.dataset;
    try {
      if (type === 'equipment') {
        await api.equipment.delete(parseInt(id, 10));
        toast('Equipment deleted');
        closeModal();
        await Promise.all([loadStats(), loadEquipment()]);
      } else {
        await api.categories.delete(parseInt(id, 10));
        toast('Category deleted');
        closeModal();
        await loadCategories();
        renderMain();
      }
    } catch (err) { toast(err.message, 'error'); }
  });
}

// Re-attach modal listeners whenever modal content changes
const modalBody = document.getElementById('modal-body');
const modalFooter = document.getElementById('modal-footer');
if (modalBody && modalFooter) {
  const observer = new MutationObserver(() => attachModalListeners());
  observer.observe(document.getElementById('modal-box'), { childList: true, subtree: true });
}

// ─── INIT ─────────────────────────────────────────────────────────────────────

async function init() {
  await loadCategories();
  await Promise.all([loadStats(), loadEquipment()]);
}

init().catch(err => {
  document.getElementById('main').innerHTML =
    `<div style="padding:40px;text-align:center;color:var(--red)">Failed to load: ${h(err.message)}</div>`;
});
