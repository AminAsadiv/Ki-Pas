// KIPAS Main JS

// ── CSRF helper ──
function getCsrf() {
  return document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

// ── Toast notifications ──
function showToast(message, type = 'success', duration = 4000) {
  const container = document.getElementById('toast-container') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast${type !== 'success' ? ' ' + type : ''}`;

  const iconMap = { success: '✓', error: '✕', warning: '⚠' };
  toast.innerHTML = `
    <span style="font-size:16px;font-weight:700;color:${type === 'success' ? 'var(--color-primary)' : type === 'error' ? 'var(--color-danger)' : 'var(--color-warning)'}">${iconMap[type] || '✓'}</span>
    <span>${message}</span>
    <button onclick="this.parentElement.remove()" style="margin-left:auto;background:none;border:none;color:var(--color-text-muted);cursor:pointer;font-size:16px;padding:0;">×</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toast-container';
  div.className = 'toast-container';
  document.body.appendChild(div);
  return div;
}

// Show Django messages as toasts
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-toast]').forEach(el => {
    showToast(el.dataset.toast, el.dataset.toastType || 'success');
    el.remove();
  });
});

// ── User dropdown ──
function toggleDropdown(id) {
  const menu = document.getElementById(id);
  if (!menu) return;
  const isOpen = !menu.classList.contains('hidden');
  document.querySelectorAll('.user-dropdown').forEach(d => d.classList.add('hidden'));
  if (!isOpen) {
    menu.classList.remove('hidden');
    // setTimeout defers listener so the current click doesn't immediately close the menu
    setTimeout(() => {
      document.addEventListener('click', function close(e) {
        if (!menu.parentElement?.contains(e.target)) {
          menu.classList.add('hidden');
          document.removeEventListener('click', close);
        }
      });
    }, 0);
  }
}

// ── Post/delete with CSRF ──
async function postTo(url, data = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: JSON.stringify(data),
  });
  return res.json().catch(() => ({}));
}

async function deleteTo(url) {
  const res = await fetch(url, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': getCsrf() },
  });
  return res.json().catch(() => ({}));
}

// ── Like event ──
function likeEvent(eventId, btn) {
  postTo(`/events/${eventId}/like/`).then(data => {
    if (data.error) { showToast(data.error, 'error'); return; }
    btn.classList.toggle('active', data.liked);
    const count = btn.querySelector('.like-count');
    if (count) count.textContent = data.count;
    showToast(data.liked ? 'Added to likes!' : 'Removed from likes');
  });
}

// ── Save event ──
function saveEvent(eventId, btn) {
  postTo(`/events/${eventId}/save/`).then(data => {
    if (data.error) { showToast(data.error, 'error'); return; }
    btn.classList.toggle('active', data.saved);
    showToast(data.saved ? 'Event saved!' : 'Removed from saved');
  });
}

// ── Join event ──
function joinEvent(eventId, btn) {
  postTo(`/events/${eventId}/join/`).then(data => {
    if (data.error) { showToast(data.error, 'error'); return; }
    btn.textContent = data.status === 'approved' ? 'Leave' : (data.status === 'pending' ? 'Pending...' : 'On Waitlist');
    btn.classList.remove('not-joined');
    btn.classList.add('joined');
    showToast(data.status === 'approved' ? 'You joined the event!' : data.status === 'pending' ? 'Request sent!' : 'Added to waitlist');
  });
}

// ── Follow user ──
function followUser(username, btn) {
  postTo(`/social/follow/${username}/`).then(data => {
    if (data.error) { showToast(data.error, 'error'); return; }
    btn.textContent = data.following ? 'Following' : 'Follow';
    btn.classList.toggle('btn-outline', data.following);
    btn.classList.toggle('btn-primary', !data.following);
    showToast(data.following ? 'Now following!' : 'Unfollowed');
  });
}

// ── Friend request ──
function sendFriendRequest(username, btn) {
  postTo(`/social/friend/${username}/`).then(data => {
    if (data.error) { showToast(data.error, 'error'); return; }
    btn.textContent = 'Request Sent';
    btn.disabled = true;
    showToast('Friend request sent!');
  });
}

// ── Mark notification read ──
function markNotifRead(id, el) {
  postTo(`/notifications/${id}/read/`).then(() => {
    el.classList.remove('unread');
  });
}

// ── Mark all read ──
function markAllNotifRead() {
  postTo('/notifications/read-all/').then(() => {
    document.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
    const badge = document.getElementById('notif-badge');
    if (badge) badge.remove();
    showToast('All notifications marked as read');
  });
}

// ── Animated counters ──
function animateCounter(el) {
  const target = parseInt(el.dataset.target, 10);
  const duration = 1500;
  const start = performance.now();
  function update(time) {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(eased * target).toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ── Intersection Observer for counters ──
document.addEventListener('DOMContentLoaded', () => {
  const counters = document.querySelectorAll('[data-counter]');
  if (!counters.length) return;
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animateCounter(e.target);
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.3 });
  counters.forEach(el => obs.observe(el));
});

// ── Tab switching ──
function switchTab(tabId, container) {
  const parent = document.getElementById(container) || document;
  parent.querySelectorAll('.tab-content').forEach(tc => tc.classList.add('hidden'));
  parent.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  const content = document.getElementById('tab-' + tabId);
  const tabBtn = document.querySelector(`[data-tab="${tabId}"]`);
  if (content) content.classList.remove('hidden');
  if (tabBtn) tabBtn.classList.add('active');
}

// ── Navbar scroll effect ──
window.addEventListener('scroll', () => {
  const nav = document.querySelector('.navbar');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 10);
});

// ── Form real-time validation ──
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-validate]').forEach(input => {
    input.addEventListener('input', () => validateField(input));
    input.addEventListener('blur', () => validateField(input));
  });
});

function validateField(input) {
  const rule = input.dataset.validate;
  const errorEl = document.getElementById(input.id + '-error');
  let error = '';

  if (rule === 'required' && !input.value.trim()) error = 'This field is required.';
  else if (rule === 'email' && input.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value)) error = 'Enter a valid email.';
  else if (rule === 'password' && input.value && input.value.length < 8) error = 'Password must be at least 8 characters.';
  else if (rule === 'username' && input.value && !/^[a-zA-Z0-9_]{3,}$/.test(input.value)) error = 'Username: 3+ chars, letters/numbers/underscores only.';

  if (errorEl) {
    errorEl.textContent = error;
    errorEl.style.display = error ? 'flex' : 'none';
  }
  input.style.borderColor = error ? 'var(--color-danger)' : '';
  return !error;
}

// ── Image preview ──
function previewImage(input, previewId) {
  const preview = document.getElementById(previewId);
  if (!preview || !input.files[0]) return;
  const reader = new FileReader();
  reader.onload = e => {
    preview.src = e.target.result;
    preview.style.display = 'block';
  };
  reader.readAsDataURL(input.files[0]);
}

// ── Modal ──
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('modal-open');
    document.body.style.overflow = 'hidden';
  }
}
function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('modal-open');
    document.body.style.overflow = '';
  }
}

// Close modal on backdrop click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.closest('.modal-wrap')?.querySelectorAll('[id]').forEach(el => closeModal(el.id));
  }
});

// ── Copy to clipboard ──
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = orig; }, 2000);
    showToast('Copied to clipboard!');
  });
}
