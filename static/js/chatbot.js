document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('ai-chat-toggle');
  const panel = document.getElementById('ai-chat-panel');
  const closeBtn = document.getElementById('ai-chat-close');
  const form = document.getElementById('ai-chat-form');
  const input = document.getElementById('ai-chat-input');
  const log = document.getElementById('ai-chat-messages');

  if (!toggleBtn || !panel || !form || !input || !log) return;

  // Initialize ARIA state
  toggleBtn.setAttribute('aria-expanded', panel.hidden ? 'false' : 'true');

  const appendMessage = (text, role) => {
    const item = document.createElement('div');
    item.className = `ai-chat-msg ${role}`;
    item.textContent = text;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
  };

  const openPanel = () => {
    panel.hidden = false;
    panel.style.display = 'flex';
    toggleBtn.setAttribute('aria-expanded', 'true');
    input.focus();
  };

  const closePanel = () => {
    panel.hidden = true;
    panel.style.display = 'none';
    toggleBtn.setAttribute('aria-expanded', 'false');
    toggleBtn.focus();
  };

  // Toggle open/close from main button
  toggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    if (panel.hidden) {
      openPanel();
    } else {
      closePanel();
    }
  });
  closeBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    closePanel();
  });

  // Close on Escape key when panel is open
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !panel.hidden) {
      closePanel();
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    appendMessage(message, 'user');
    input.value = '';

    try {
      const res = await fetch('/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      const data = await res.json();
      if (!res.ok) {
        const errMsg = data.error || `Error: ${res.status}`;
        appendMessage(`Assistant error: ${errMsg}`, 'bot');
      } else {
        appendMessage(data.reply || 'No reply received.', 'bot');
      }
    } catch (err) {
      console.error('Chatbot error:', err);
      appendMessage(`Network error: ${err.message}`, 'bot');
    }
  });

  // Initial greeting only (shows once when panel loads)
  appendMessage('Hi! 👋 I know your profile details and can help with expenses, weekly reports, and tuition reminders.', 'bot');
});
