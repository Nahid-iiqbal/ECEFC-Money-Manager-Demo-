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

  /**
   * Safely render markdown for bot messages, plain text for user
   * @param {string} text - Message content
   * @param {string} role - 'user' or 'bot'
   */
  const renderMarkdownSafe = (text, role) => {
    // User messages: always plain text (no XSS risk)
    if (role === 'user') {
      return text; // Will be set via textContent
    }

    // Bot messages: try markdown rendering with sanitization
    try {
      if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
        // Configure marked for GFM (GitHub Flavored Markdown) with line breaks
        const rawHtml = marked.parse(text, {
          breaks: true,        // Convert \n to <br>
          gfm: true,           // GitHub Flavored Markdown
          headerIds: false,    // Don't add IDs to headers
          mangle: false        // Don't escape email addresses
        });

        // Sanitize HTML to prevent XSS
        const cleanHtml = DOMPurify.sanitize(rawHtml, {
          ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'a', 'ul', 'ol', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
          ALLOWED_ATTR: ['href', 'target', 'rel'],
          ALLOW_DATA_ATTR: false
        });

        // Add target and rel to external links for security
        const temp = document.createElement('div');
        temp.innerHTML = cleanHtml;
        temp.querySelectorAll('a[href]').forEach(link => {
          if (link.href.startsWith('http')) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
          }
        });

        return temp.innerHTML;
      }
    } catch (err) {
      console.warn('Markdown rendering failed, falling back to plain text:', err);
    }

    // Fallback: escape HTML and preserve line breaks
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
      .replace(/\n/g, '<br>');
  };

  const appendMessage = (text, role) => {
    const item = document.createElement('div');
    item.className = `ai-chat-msg ${role}`;
    
    if (role === 'user') {
      // User messages: plain text only (safe)
      item.textContent = text;
    } else {
      // Bot messages: rendered markdown (sanitized)
      item.innerHTML = renderMarkdownSafe(text, role);
    }
    
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

  // ===== RESIZE FUNCTIONALITY =====
  
  const STORAGE_KEY = 'finbuddy-chat-size';
  const MIN_WIDTH = 320;
  const MIN_HEIGHT = 420;
  const MAX_WIDTH_VW = 50;
  const MAX_HEIGHT_VH = 50;
  const MAX_WIDTH_PX = 720;
  const MAX_HEIGHT_PX = 720;

  let isResizing = false;
  let resizeDirection = null;
  let startX = 0;
  let startY = 0;
  let startWidth = 0;
  let startHeight = 0;
  let rafId = null;

  const resizeHandles = document.querySelectorAll('.ai-chat-resize-handle');

  /**
   * Get max dimensions based on viewport
   */
  const getMaxDimensions = () => ({
    width: Math.min(window.innerWidth * MAX_WIDTH_VW / 100, MAX_WIDTH_PX),
    height: Math.min(window.innerHeight * MAX_HEIGHT_VH / 100, MAX_HEIGHT_PX)
  });

  /**
   * Clamp value between min and max
   */
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  /**
   * Load saved size from localStorage
   */
  const loadSize = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const size = JSON.parse(saved);
        const maxDims = getMaxDimensions();
        
        const width = clamp(size.width, MIN_WIDTH, maxDims.width);
        const height = clamp(size.height, MIN_HEIGHT, maxDims.height);
        
        panel.style.width = `${width}px`;
        panel.style.height = `${height}px`;
        
        return true;
      }
    } catch (err) {
      console.warn('Failed to load chat size:', err);
    }
    return false;
  };

  /**
   * Save current size to localStorage
   */
  const saveSize = () => {
    try {
      const size = {
        width: panel.offsetWidth,
        height: panel.offsetHeight
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(size));
    } catch (err) {
      console.warn('Failed to save chat size:', err);
    }
  };

  // ===== RESIZE FUNCTIONALITY =====
  
  const startResize = (e) => {
    // Determine which corner is being dragged
    if (e.target.classList.contains('ai-resize-bl')) {
      resizeDirection = 'bl'; // bottom-left
    } else if (e.target.classList.contains('ai-resize-tr')) {
      resizeDirection = 'tr'; // top-right
    } else if (e.target.classList.contains('ai-resize-tl')) {
      resizeDirection = 'tl'; // top-left
    } else {
      return;
    }

    isResizing = true;
    startX = e.clientX;
    startY = e.clientY;
    startWidth = panel.offsetWidth;
    startHeight = panel.offsetHeight;
    
    document.body.style.userSelect = 'none';
    e.preventDefault();
    e.stopPropagation();
  };

  const doResize = (e) => {
    if (!isResizing) return;
    
    const maxDims = getMaxDimensions();
    const deltaX = e.clientX - startX;
    const deltaY = e.clientY - startY;
    
    let newWidth = startWidth;
    let newHeight = startHeight;
    
    // Calculate new dimensions based on corner direction
    if (resizeDirection === 'bl') {
      // Bottom-left: width decreases when dragging right, height increases when dragging down
      newWidth = startWidth - deltaX;
      newHeight = startHeight + deltaY;
    } else if (resizeDirection === 'tr') {
      // Top-right: width increases when dragging right, height decreases when dragging up
      newWidth = startWidth + deltaX;
      newHeight = startHeight - deltaY;
    } else if (resizeDirection === 'tl') {
      // Top-left: both decrease when dragging right/down
      newWidth = startWidth - deltaX;
      newHeight = startHeight - deltaY;
    }
    
    // Clamp dimensions
    newWidth = clamp(newWidth, MIN_WIDTH, maxDims.width);
    newHeight = clamp(newHeight, MIN_HEIGHT, maxDims.height);
    
    panel.style.width = `${newWidth}px`;
    panel.style.height = `${newHeight}px`;
  };

  const resize = (e) => {
    if (!isResizing) return;
    
    if (rafId) {
      cancelAnimationFrame(rafId);
    }
    
    rafId = requestAnimationFrame(() => {
      doResize(e);
      rafId = null;
    });
  };

  const endResize = () => {
    if (isResizing) {
      isResizing = false;
      resizeDirection = null;
      document.body.style.userSelect = '';
      
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      
      saveSize();
    }
  };

  // ===== EVENT LISTENERS =====
  
  resizeHandles.forEach(handle => {
    handle.addEventListener('pointerdown', startResize);
  });

  document.addEventListener('pointermove', resize);
  document.addEventListener('pointerup', endResize);
  document.addEventListener('pointercancel', endResize);

  // Re-clamp on window resize
  window.addEventListener('resize', () => {
    if (!panel.hidden) {
      loadSize();
    }
  });

  // Load saved size when panel opens
  const originalOpenPanel = openPanel;
  openPanel = () => {
    originalOpenPanel();
    loadSize();
  };
});
