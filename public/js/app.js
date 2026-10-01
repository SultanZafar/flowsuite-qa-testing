const API = '/api';

let state = {
  token: localStorage.getItem('tf_token') || null,
  user: JSON.parse(localStorage.getItem('tf_user') || 'null'),
  orgs: [],
  currentOrgId: null,
  currentProjectId: null,
};

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) headers['Authorization'] = 'Bearer ' + state.token;
  const res = await fetch(API + path, { ...options, headers: { ...headers, ...(options.headers || {}) } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str == null ? '' : str;
  return div.innerHTML;
}

// ---------- boot ----------
window.addEventListener('DOMContentLoaded', () => {
  if (state.token && state.user) {
    enterApp();
  }
});

// ---------- auth tabs ----------
document.querySelectorAll('.auth-tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.auth-tab').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('form-login').style.display = tab.dataset.tab === 'login' ? 'block' : 'none';
    document.getElementById('form-signup').style.display = tab.dataset.tab === 'signup' ? 'block' : 'none';
  });
});

document.getElementById('btn-login').addEventListener('click', async () => {
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const errorEl = document.getElementById('login-error');
  errorEl.textContent = '';
  try {
    const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    persistAuth(data.token, data.user);
    enterApp();
  } catch (e) {
    errorEl.textContent = e.error || 'Login failed';
  }
});

document.getElementById('btn-signup').addEventListener('click', async () => {
  const name = document.getElementById('signup-name').value.trim();
  const email = document.getElementById('signup-email').value.trim();
  const password = document.getElementById('signup-password').value;
  const orgName = document.getElementById('signup-orgname').value.trim();
  const errorEl = document.getElementById('signup-error');
  errorEl.textContent = '';
  try {
    const data = await api('/auth/signup', { method: 'POST', body: JSON.stringify({ name, email, password, orgName }) });
    persistAuth(data.token, data.user);
    enterApp();
  } catch (e) {
    errorEl.textContent = e.error || 'Signup failed';
  }
});

function persistAuth(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem('tf_token', token);
  localStorage.setItem('tf_user', JSON.stringify(user));
}

document.getElementById('btn-logout').addEventListener('click', () => {
  localStorage.removeItem('tf_token');
  localStorage.removeItem('tf_user');
  state = { token: null, user: null, orgs: [], currentOrgId: null, currentProjectId: null };
  document.getElementById('view-app').style.display = 'none';
  document.getElementById('view-auth').style.display = 'flex';
});

// ---------- enter app ----------
async function enterApp() {
  document.getElementById('view-auth').style.display = 'none';
  document.getElementById('view-app').style.display = 'flex';
  document.getElementById('current-user-name').textContent = state.user.name + ' (' + state.user.email + ')';

  const data = await api('/orgs');
  state.orgs = data.orgs;

  const select = document.getElementById('org-select');
  select.innerHTML = state.orgs.map((o) => `<option value="${o.org_id}">${escapeHtml(o.name)} — ${o.role}</option>`).join('');

  state.currentOrgId = state.orgs.length ? state.orgs[0].org_id : null;
  select.value = state.currentOrgId;

  showTab('projects');
}

document.getElementById('org-select').addEventListener('change', (e) => {
  state.currentOrgId = Number(e.target.value);
  showTab('projects');
});

// ---------- tab switching ----------
document.querySelectorAll('.nav-item[data-tab]').forEach((item) => {
  item.addEventListener('click', () => showTab(item.dataset.tab));
});

function showTab(tabName) {
  document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
  document.getElementById('tab-' + tabName).classList.add('active');
  document.querySelectorAll('.nav-item[data-tab]').forEach((n) => n.classList.remove('active'));
  const navItem = document.querySelector(`.nav-item[data-tab="${tabName}"]`);
  if (navItem) navItem.classList.add('active');

  if (tabName === 'projects') loadProjects();
  if (tabName === 'members') loadMembers();
  if (tabName === 'billing') loadBilling();
}

// ---------- projects ----------
async function loadProjects() {
  const data = await api(`/orgs/${state.currentOrgId}/projects`);
  const list = document.getElementById('project-list');
  list.innerHTML = data.projects
    .map(
      (p) => `
    <div class="project-card" data-project-id="${p.project_id}" data-testid="project-card-${p.project_id}">
      <h3>${escapeHtml(p.name)}</h3>
      <div class="meta">Org ID: ${p.org_id} · Created ${new Date(p.created_at).toLocaleDateString()}</div>
    </div>`
    )
    .join('') || '<p style="color:#999;">No projects yet.</p>';

  list.querySelectorAll('.project-card').forEach((card) => {
    card.addEventListener('click', () => openProject(card.dataset.projectId, card.querySelector('h3').textContent));
  });
}

document.getElementById('btn-new-project').addEventListener('click', async () => {
  const name = prompt('Project name:');
  if (!name) return;
  try {
    await api(`/orgs/${state.currentOrgId}/projects`, { method: 'POST', body: JSON.stringify({ name }) });
    loadProjects();
  } catch (e) {
    showToast(e.error || 'Failed to create project');
  }
});

// ---------- project detail / tasks ----------
async function openProject(projectId, name) {
  state.currentProjectId = projectId;
  document.getElementById('project-detail-name').textContent = name;

  const members = await api(`/orgs/${state.currentOrgId}/members`);
  const assigneeSelect = document.getElementById('new-task-assignee');
  assigneeSelect.innerHTML =
    '<option value="">Unassigned</option>' +
    members.members.map((m) => `<option value="${m.user_id}">${escapeHtml(m.name)}</option>`).join('');

  document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
  document.getElementById('tab-project-detail').classList.add('active');

  loadTasks();
}

document.getElementById('btn-back-to-projects').addEventListener('click', () => showTab('projects'));

async function loadTasks() {
  const data = await api(`/orgs/${state.currentOrgId}/projects/${state.currentProjectId}/tasks`);
  const list = document.getElementById('task-list');
  list.innerHTML = data.tasks
    .map(
      (t) => `
    <div class="task-item" data-testid="task-item-${t.task_id}">
      <div>
        <div class="task-title">${escapeHtml(t.title)}</div>
        <div class="task-meta">${t.assignee_name ? 'Assigned to ' + escapeHtml(t.assignee_name) : 'Unassigned'}</div>
      </div>
      <div class="task-actions">
        <span class="task-status ${t.status}" data-task-id="${t.task_id}" data-status="${t.status}" data-testid="task-status-${t.task_id}">${t.status.replace('_', ' ')}</span>
        <span class="delete-task" data-task-id="${t.task_id}" data-testid="delete-task-${t.task_id}">Delete</span>
      </div>
    </div>`
    )
    .join('') || '<p style="color:#999;">No tasks yet.</p>';

  const flow = { TODO: 'IN_PROGRESS', IN_PROGRESS: 'DONE', DONE: 'TODO' };
  list.querySelectorAll('.task-status').forEach((el) =>
    el.addEventListener('click', async () => {
      const next = flow[el.dataset.status];
      await api(`/orgs/${state.currentOrgId}/tasks/${el.dataset.taskId}`, { method: 'PATCH', body: JSON.stringify({ status: next }) });
      loadTasks();
    })
  );
  list.querySelectorAll('.delete-task').forEach((el) =>
    el.addEventListener('click', async () => {
      await api(`/orgs/${state.currentOrgId}/tasks/${el.dataset.taskId}`, { method: 'DELETE' });
      loadTasks();
    })
  );
}

document.getElementById('btn-add-task').addEventListener('click', async () => {
  const title = document.getElementById('new-task-title').value.trim();
  const assigneeId = document.getElementById('new-task-assignee').value;
  if (!title) return;
  try {
    await api(`/orgs/${state.currentOrgId}/projects/${state.currentProjectId}/tasks`, {
      method: 'POST',
      body: JSON.stringify({ title, assigneeId: assigneeId ? Number(assigneeId) : null }),
    });
    document.getElementById('new-task-title').value = '';
    loadTasks();
  } catch (e) {
    showToast(e.error || 'Failed to add task');
  }
});

// ---------- members ----------
async function loadMembers() {
  const data = await api(`/orgs/${state.currentOrgId}/members`);
  const list = document.getElementById('members-list');
  list.innerHTML = data.members
    .map(
      (m) => `
    <div class="member-row" data-testid="member-row-${m.user_id}">
      <div class="member-info">
        <div class="name">${escapeHtml(m.name)}</div>
        <div class="email">${escapeHtml(m.email)}</div>
      </div>
      <select class="role-select" data-user-id="${m.user_id}" data-testid="role-select-${m.user_id}">
        <option value="MEMBER" ${m.role === 'MEMBER' ? 'selected' : ''}>Member</option>
        <option value="ADMIN" ${m.role === 'ADMIN' ? 'selected' : ''}>Admin</option>
        <option value="OWNER" ${m.role === 'OWNER' ? 'selected' : ''}>Owner</option>
      </select>
    </div>`
    )
    .join('');

  list.querySelectorAll('.role-select').forEach((sel) =>
    sel.addEventListener('change', async () => {
      try {
        await api(`/orgs/${state.currentOrgId}/members/${sel.dataset.userId}/role`, {
          method: 'PATCH',
          body: JSON.stringify({ role: sel.value }),
        });
        showToast('Role updated');
      } catch (e) {
        showToast(e.error || 'Failed to update role');
      }
    })
  );
}

document.getElementById('btn-invite-member').addEventListener('click', () => {
  const form = document.getElementById('invite-form');
  form.style.display = form.style.display === 'none' ? 'flex' : 'none';
});

document.getElementById('btn-submit-invite').addEventListener('click', async () => {
  const name = document.getElementById('invite-name').value.trim();
  const email = document.getElementById('invite-email').value.trim();
  const role = document.getElementById('invite-role').value;
  if (!name || !email) return;
  try {
    await api(`/orgs/${state.currentOrgId}/members/invite`, { method: 'POST', body: JSON.stringify({ name, email, role }) });
    document.getElementById('invite-name').value = '';
    document.getElementById('invite-email').value = '';
    document.getElementById('invite-form').style.display = 'none';
    showToast('Member invited');
    loadMembers();
  } catch (e) {
    showToast(e.error || 'Failed to invite member');
  }
});

// ---------- billing ----------
async function loadBilling() {
  const sub = await api(`/orgs/${state.currentOrgId}/subscription`);
  document.getElementById('subscription-card').innerHTML = `
    <div class="plan-name" data-testid="current-plan-name">${sub.plan} Plan</div>
    <span class="status-badge" data-testid="current-plan-status">${sub.status}</span>
    ${sub.trial_ends_at ? `<div style="margin-top:8px;font-size:12px;color:#999;">Trial ends: ${new Date(sub.trial_ends_at).toLocaleDateString()}</div>` : ''}
  `;

  const invoicesData = await api(`/orgs/${state.currentOrgId}/invoices`);
  document.getElementById('invoice-list').innerHTML =
    invoicesData.invoices
      .map(
        (inv) => `
      <div class="invoice-row" data-testid="invoice-row-${inv.invoice_id}">
        <span>${inv.plan} plan — ${new Date(inv.created_at).toLocaleDateString()}</span>
        <span>$${inv.amount.toFixed(2)} · ${inv.status}</span>
      </div>`
      )
      .join('') || '<div class="invoice-row" style="color:#999;">No invoices yet.</div>';
}

document.querySelectorAll('.btn-select-plan').forEach((btn) => {
  btn.addEventListener('click', async () => {
    try {
      const result = await api(`/orgs/${state.currentOrgId}/subscription/upgrade`, {
        method: 'POST',
        body: JSON.stringify({ plan: btn.dataset.plan }),
      });
      showToast(`Switched to ${result.plan} — charged $${result.amountCharged}`);
      loadBilling();
    } catch (e) {
      showToast(e.error || 'Failed to change plan');
    }
  });
});

document.getElementById('btn-cancel-sub').addEventListener('click', async () => {
  if (!confirm('Cancel your subscription?')) return;
  await api(`/orgs/${state.currentOrgId}/subscription/cancel`, { method: 'POST' });
  showToast('Subscription canceled');
  loadBilling();
});
