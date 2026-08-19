// KIPAS Map

let kipasMap = null;
let markersLayer = null;
let userMarker = null;
let selectedEventId = null;

function initMap() {
  kipasMap = L.map('map', {
    center: [51.505, -0.09],
    zoom: 13,
    zoomControl: false,
  });

  // Dark tile layer (CartoDB Dark Matter)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors © CARTO',
    subdomains: 'abcd',
    maxZoom: 19,
  }).addTo(kipasMap);

  // Custom zoom control
  L.control.zoom({ position: 'bottomright' }).addTo(kipasMap);

  // Marker cluster group
  markersLayer = L.markerClusterGroup({
    iconCreateFunction: function (cluster) {
      return L.divIcon({
        html: `<div class="marker-cluster" style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#050761;border:2px solid #40FFA7;color:#40FFA7;font-weight:700;font-size:13px;box-shadow:0 4px 12px rgba(64,255,167,0.3);">${cluster.getChildCount()}</div>`,
        className: '',
        iconSize: [40, 40],
      });
    },
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    spiderfyOnMaxZoom: true,
    disableClusteringAtZoom: 17,
  });
  kipasMap.addLayer(markersLayer);

  // Get user location
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      const { latitude, longitude } = pos.coords;
      kipasMap.setView([latitude, longitude], 13);
      addUserMarker(latitude, longitude);
    }, null, { timeout: 5000 });
  }

  // Right-click to create event
  kipasMap.on('contextmenu', e => {
    showContextMenu(e.latlng, e.containerPoint);
  });

  // Load events
  loadEvents();
}

function addUserMarker(lat, lng) {
  if (userMarker) userMarker.remove();
  const icon = L.divIcon({
    html: '<div class="user-location-marker"></div>',
    className: '',
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
  userMarker = L.marker([lat, lng], { icon }).addTo(kipasMap);
  userMarker.bindTooltip('You are here', { permanent: false, direction: 'top' });
}

function createEventIcon(category) {
  const iconMap = {
    'sports': '⚽', 'entertainment': '🎭', 'education': '📚',
    'technology': '💻', 'business': '💼', 'arts': '🎨',
    'food': '🍕', 'travel': '✈️', 'community': '🤝',
    'lifestyle': '🧘', 'social': '👥', 'health': '💚',
    'default': '📍',
  };
  const emoji = iconMap[category?.toLowerCase()] || iconMap.default;
  return L.divIcon({
    html: `<div class="kipas-marker">
      <div class="kipas-marker-circle">
        <span style="font-size:14px;">${emoji}</span>
      </div>
      <div class="kipas-marker-stem"></div>
    </div>`,
    className: '',
    iconSize: [40, 48],
    iconAnchor: [20, 48],
  });
}

function loadEvents(filters = {}) {
  markersLayer.clearLayers();
  const bounds = kipasMap.getBounds();
  const params = new URLSearchParams({
    sw_lat: bounds.getSouthWest().lat,
    sw_lng: bounds.getSouthWest().lng,
    ne_lat: bounds.getNorthEast().lat,
    ne_lng: bounds.getNorthEast().lng,
    ...filters,
  });

  fetch(`/api/v1/map/events/?${params}`)
    .then(r => r.json())
    .then(data => {
      (data.events || data.results || []).forEach(event => {
        if (!event.latitude || !event.longitude) return;
        const marker = L.marker([event.latitude, event.longitude], {
          icon: createEventIcon(event.category_slug),
        });
        marker.on('click', () => showEventPanel(event));
        markersLayer.addLayer(marker);
      });
    })
    .catch(() => {});
}

function showEventPanel(event) {
  selectedEventId = event.id;
  const panel = document.getElementById('map-event-panel');
  if (!panel) return;

  const cover = event.cover_image
    ? `<img src="${event.cover_image}" class="map-event-cover" alt="${event.title}">`
    : `<div class="map-event-cover" style="background:linear-gradient(135deg,#050761,#1a0b4d);display:flex;align-items:center;justify-content:center;font-size:40px;">📍</div>`;

  panel.innerHTML = `
    <div style="position:relative;">
      ${cover}
      <button class="map-event-close" onclick="closeEventPanel()">✕</button>
    </div>
    <div class="map-event-body">
      <div class="flex items-center gap-2 mb-2">
        <span class="badge badge-primary">${event.category_name || 'Event'}</span>
        <span class="badge badge-surface" style="font-size:11px;">${event.event_type || 'Free'}</span>
      </div>
      <h3 style="font-size:18px;margin-bottom:8px;">${event.title}</h3>
      <div style="display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--color-text-muted);margin-bottom:16px;">
        <div class="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          ${new Date(event.start_datetime).toLocaleDateString('en-US', {weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
        </div>
        <div class="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          ${event.location_name || event.address || 'Location TBD'}
        </div>
        <div class="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          ${event.participant_count || 0} joined${event.capacity ? ` / ${event.capacity}` : ''}
        </div>
      </div>
      <div class="flex gap-2">
        <a href="/events/${event.id}/" class="btn btn-primary btn-sm flex-1 text-center">View Details</a>
        <button onclick="joinEvent(${event.id}, this)" class="btn btn-outline btn-sm">Join</button>
      </div>
    </div>
  `;
  panel.classList.add('visible');
}

function closeEventPanel() {
  const panel = document.getElementById('map-event-panel');
  if (panel) panel.classList.remove('visible');
  selectedEventId = null;
}

function showContextMenu(latlng, point) {
  hideContextMenu();
  const menu = document.createElement('div');
  menu.className = 'map-ctx-menu';
  menu.id = 'map-ctx-menu';
  menu.style.left = point.x + 'px';
  menu.style.top = point.y + 'px';
  menu.innerHTML = `
    <div class="map-ctx-item" onclick="createEventHere(${latlng.lat}, ${latlng.lng})">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
      Create Event Here
    </div>
    <div class="map-ctx-item" onclick="hideContextMenu()">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="10" r="3"/><path d="M12 2a8 8 0 0 0-8 8c0 5.4 7.1 11.6 7.4 11.9a1 1 0 0 0 1.2 0C12.9 21.6 20 15.4 20 10a8 8 0 0 0-8-8z"/></svg>
      Drop a Pin
    </div>
  `;
  document.getElementById('map').appendChild(menu);
  setTimeout(() => document.addEventListener('click', hideContextMenu, { once: true }), 50);
}

function hideContextMenu() {
  document.getElementById('map-ctx-menu')?.remove();
}

function createEventHere(lat, lng) {
  hideContextMenu();
  window.location.href = `/events/create/?lat=${lat}&lng=${lng}`;
}

// Category filter
function filterByCategory(slug) {
  document.querySelectorAll('.filter-pill').forEach(p => p.classList.toggle('active', p.dataset.cat === slug));
  loadEvents(slug ? { category: slug } : {});
}

// Reload on map move
document.addEventListener('DOMContentLoaded', () => {
  if (!document.getElementById('map')) return;
  initMap();
  kipasMap.on('moveend', () => loadEvents(getActiveFilters()));
});

function getActiveFilters() {
  const active = document.querySelector('.filter-pill.active');
  return active ? { category: active.dataset.cat } : {};
}
