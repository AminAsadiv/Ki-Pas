// KIPAS Chat — WebSocket with HTTP fallback

let chatSocket = null;
let conversationId = null;
let currentUserId = null;
let typingTimer = null;
let reconnectDelay = 2000;
let wsReady = false;

function initChat(convId, userId) {
  conversationId = convId;
  currentUserId = userId;
  _connectWS();
}

function _connectWS() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  chatSocket = new WebSocket(`${protocol}//${location.host}/ws/chat/${conversationId}/`);

  chatSocket.onopen = () => {
    wsReady = true;
    reconnectDelay = 2000;
    document.getElementById('send-btn')?.removeAttribute('disabled');
  };

  chatSocket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'message.new') {
      // Don't duplicate messages we sent ourselves via HTTP fallback
      if (String(data.message.sender_id) !== String(currentUserId)) {
        appendMessage(data.message);
      }
    } else if (data.type === 'typing') {
      handleTyping(data);
    } else if (data.type === 'presence') {
      handlePresence(data);
    }
  };

  chatSocket.onclose = () => {
    wsReady = false;
    setTimeout(_connectWS, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 1.5, 30000);
  };

  chatSocket.onerror = () => { wsReady = false; };
}

// Called from template — replyToId injected by template override
function sendMessage(replyToId) {
  const input = document.getElementById('chat-input');
  if (!input || !input.value.trim()) return;

  const content = input.value.trim();
  const payload = { type: 'message.new', content };
  if (replyToId) payload.reply_to_id = replyToId;

  if (wsReady && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
    // WebSocket path — server will echo back via group_send
    chatSocket.send(JSON.stringify(payload));
    // Optimistically render own message immediately
    appendMessage({
      id: Date.now(),
      content,
      sender_id: currentUserId,
      sender_username: window._myUsername || '',
      sender_avatar: window._myAvatar || '',
      created_at: new Date().toISOString(),
      message_type: 'text',
      reply_to: null,
    });
  } else {
    // HTTP fallback
    const body = new URLSearchParams({ content });
    if (replyToId) body.append('reply_to_id', replyToId);
    fetch(`/messages/${conversationId}/send/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': _getCsrf(), 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    }).then(r => r.json()).then(d => {
      if (d.ok) appendMessage(d.message);
    });
  }

  input.value = '';
  input.style.height = 'auto';
  sendTyping(false);
}

function sendTyping(isTyping) {
  if (!wsReady || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;
  chatSocket.send(JSON.stringify({ type: isTyping ? 'typing.start' : 'typing.stop' }));
}

function appendMessage(msg) {
  const container = document.getElementById('messages-container');
  if (!container) return;

  const isOwn = String(msg.sender_id) === String(currentUserId);
  const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // Hide typing indicator
  const ti = document.getElementById('typing-indicator');
  if (ti) ti.style.display = 'none';

  const row = document.createElement('div');
  row.className = `msg-row${isOwn ? ' own' : ''}`;
  row.id = 'msg-' + msg.id;
  row.dataset.id = msg.id;
  row.dataset.content = (msg.content || '').slice(0, 80);
  row.dataset.sender = msg.sender_username;

  const avatarHtml = isOwn ? '' : msg.sender_avatar
    ? `<div class="msg-avatar-col"><img src="${msg.sender_avatar}" class="msg-avatar" alt="${_esc(msg.sender_username)}"></div>`
    : `<div class="msg-avatar-col"><div class="msg-avatar msg-avatar-placeholder">${(msg.sender_username || '?')[0].toUpperCase()}</div></div>`;

  const replyHtml = msg.reply_to
    ? `<div class="msg-reply-preview"><div class="msg-reply-author">${_esc(msg.reply_to.sender_username)}</div><div class="msg-reply-text">${_esc(msg.reply_to.content)}</div></div>`
    : '';

  const senderLabel = (!isOwn && typeof IS_GROUP !== 'undefined' && IS_GROUP)
    ? `<div class="msg-group-sender">${_esc(msg.sender_username)}</div>`
    : '';

  row.innerHTML = `
    ${avatarHtml}
    <div class="msg-content-wrap">
      ${senderLabel}
      ${replyHtml}
      <div class="msg-bubble">${_esc(msg.content)}</div>
      <div class="msg-meta">
        ${time}
        ${isOwn ? '<span class="msg-receipt" title="Sent"><i data-lucide="check-check" width="11" height="11"></i></span>' : ''}
      </div>
    </div>
    <div class="msg-actions">
      <button class="msg-action-btn" onclick="setReply(${msg.id},'${_esc(msg.sender_username)}','${_esc(msg.content).slice(0,60)}')" title="Reply">
        <i data-lucide="corner-up-left" width="13" height="13"></i>
      </button>
      <button class="msg-action-btn" onclick="addReaction(${msg.id},this)" title="React">
        <i data-lucide="smile" width="13" height="13"></i>
      </button>
    </div>`;

  container.appendChild(row);
  if (window.lucide) lucide.createIcons({ nodes: [row] });
  scrollToBottom();
}

function handleTyping(data) {
  if (String(data.user_id) === String(currentUserId)) return;
  const indicator = document.getElementById('typing-indicator');
  if (!indicator) return;
  const avatarEl = document.getElementById('typing-avatar');
  if (data.typing) {
    if (avatarEl) avatarEl.textContent = (data.username || '?')[0].toUpperCase();
    indicator.style.display = 'flex';
    scrollToBottom();
  } else {
    indicator.style.display = 'none';
  }
}

function handlePresence(data) {
  if (String(data.user_id) === String(currentUserId)) return;
  const el = document.getElementById('chat-status-text');
  if (el) el.innerHTML = data.online ? '<span class="online-dot"></span> Active now' : 'Last seen just now';
}

function scrollToBottom() {
  const c = document.getElementById('messages-container');
  if (c) c.scrollTop = c.scrollHeight;
}

function _getCsrf() {
  return document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

function _esc(str) {
  return String(str || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#039;').replace(/\n/g, '<br>');
}
