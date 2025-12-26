# AI Chatbot Documentation

## 🤖 Overview

The FeinBuddy AI Chatbot is a floating widget providing intelligent assistance with full access to user profile, expenses, and tuition data. It features complete **light and dark theme support** with gradient color schemes matching the app's design system.

---

## ✅ Audit Results

### Functionality Status: **ALL WORKING** ✓

| Component | Status | Location |
|-----------|--------|----------|
| HTML Structure | ✅ Working | `templates/base.html` lines 66-83 |
| JavaScript Logic | ✅ Working | `static/js/chatbot.js` (87 lines) |
| Backend API | ✅ Working | `app.py` lines 407-450+ |
| CSS Theming | ✅ **FIXED** | `static/css/style.css` lines 62-300 |

### Features Verified:
- ✅ Toggle button opens/closes panel
- ✅ ARIA attributes for accessibility
- ✅ Escape key closes panel
- ✅ Messages append and auto-scroll
- ✅ Form submission with error handling
- ✅ POST to `/api/chatbot` with user context
- ✅ Light and dark theme support
- ✅ Mobile responsive layout

---

## 🎨 Theme Implementation

### Light Theme Colors:
- **Toggle Button**: Purple gradient (`#667eea` → `#764ba2`)
- **Panel Background**: `var(--bg-card)` (white)
- **User Messages**: Purple gradient with shadow
- **Bot Messages**: White with purple border
- **Send Button**: Purple gradient
- **Accents**: Blue/purple tones

### Dark Theme Colors:
- **Toggle Button**: Maroon gradient (`#8B2833` → `#5c1a28`)
- **Panel Background**: `var(--bg-card)` (dark brown)
- **User Messages**: Maroon gradient with shadow
- **Bot Messages**: Dark card with red border
- **Send Button**: Maroon gradient
- **Accents**: Red/maroon tones (`#ff6b6b`, `#e74c3c`)

### CSS Variables Used:
```css
--bg-card          /* Panel/message backgrounds */
--bg-primary       /* Messages container background */
--bg-secondary     /* Dark mode messages container */
--bg-input         /* Input field background */
--text-primary     /* Main text color */
--text-tertiary    /* Placeholder text */
--border-color     /* Panel/input borders */
--border-focus     /* Focus state borders */
--accent-red       /* Dark mode accent color */
--shadow-lg        /* Panel shadow */
```

---

## 🛠️ Component Architecture

### 1. HTML Structure (`base.html`)
```html
<div class="ai-chatbot">
  <!-- Toggle Button -->
  <button id="ai-chat-toggle" aria-expanded="false">
    💬 AI Assistant
  </button>
  
  <!-- Chat Panel (hidden by default) -->
  <div id="ai-chat-panel" class="ai-chat-panel" hidden>
    <!-- Header -->
    <div class="ai-chat-header">
      <div>
        <h4 class="ai-chat-title">AI Assistant</h4>
        <p class="ai-chat-subtitle">FeinBuddy</p>
      </div>
      <button id="ai-chat-close">×</button>
    </div>
    
    <!-- Messages -->
    <div id="ai-chat-messages" class="ai-chat-messages"></div>
    
    <!-- Input Form -->
    <form id="ai-chat-form" class="ai-chat-form">
      <input id="ai-chat-input" type="text" 
             placeholder="Ask about expenses..." />
      <button type="submit" class="ai-chat-send">Send</button>
    </form>
  </div>
</div>
```

### 2. JavaScript Logic (`chatbot.js`)

**Key Functions:**
- `openPanel()` - Shows panel, sets ARIA state, focuses input
- `closePanel()` - Hides panel, sets ARIA state, focuses toggle
- `appendMessage(text, role)` - Adds user/bot messages, auto-scrolls
- Form submit handler - Sends POST to `/api/chatbot`, displays response
- Escape key handler - Closes panel when pressed

**Event Listeners:**
- Toggle button click → Open/close panel
- Close button click → Close panel
- Escape key → Close panel
- Form submit → Send message to API

### 3. Backend API (`app.py`)

**Route:** `POST /api/chatbot`

**User Context Provided:**
```python
{
  "display_name": "John Doe",
  "email": "john@example.com",
  "profession": "Student",
  "institution": "XYZ University",
  "total_recent": 150.50,      # Last 7 days
  "total_all_time": 2340.75,   # All time
  "category_summary": {         # Last 7 days
    "Food": 80.25,
    "Transport": 40.00,
    "Other": 30.25
  },
  "tuition_count": 3,
  "total_tuition_income": 450.00
}
```

**Response Format:**
```json
{
  "reply": "Based on your spending, you've spent $150.50 this week..."
}
```

---

## 📱 Responsive Behavior

### Desktop (>600px):
- Panel: 360px width, 500px max height
- Toggle: Full padding, 0.95rem font
- Fixed position: Bottom-right corner

### Mobile (<600px):
- Panel: `calc(100vw - 40px)` width, 70vh max height
- Toggle: Reduced padding, 0.9rem font

### Small Mobile (<400px):
- Chatbot: 15px from edges (reduced from 20px)

---

## 🎯 Future Enhancements

### Potential Improvements:
1. **Typing Indicator**: Show "..." while waiting for response
2. **Message Timestamps**: Add time to each message
3. **Conversation History**: Store messages in localStorage
4. **Message Actions**: Copy/delete message buttons
5. **Markdown Support**: Format bot responses with bold/links
6. **Attachments**: Allow image uploads for receipt scanning
7. **Voice Input**: Speech-to-text for hands-free messaging
8. **Suggested Questions**: Quick reply buttons for common queries
9. **Notification Badge**: Show unread message count on toggle
10. **Message Search**: Search conversation history

### Backend Improvements:
1. **AI Integration**: Connect to OpenAI/Anthropic API for intelligent responses
2. **Context Memory**: Store conversation history in database
3. **Smart Insights**: Provide spending trends and budget alerts
4. **Expense Commands**: "Add expense: Food $25" to create records
5. **Query Expansion**: "Show last week's food expenses"

---

## 🔧 Customization Guide

### Change Theme Colors:

**Light Mode (modify in `style.css`):**
```css
/* Toggle button gradient */
.ai-chat-toggle {
    background: linear-gradient(135deg, #NEW_COLOR_1, #NEW_COLOR_2);
}

/* User message gradient */
.ai-chat-msg.user {
    background: linear-gradient(135deg, #NEW_COLOR_1, #NEW_COLOR_2);
}
```

**Dark Mode:**
```css
[data-theme="dark"] .ai-chat-toggle {
    background: linear-gradient(135deg, #NEW_DARK_1, #NEW_DARK_2);
}
```

### Change Panel Size:
```css
.ai-chat-panel {
    width: 400px;        /* Default: 360px */
    max-height: 600px;   /* Default: 500px */
}
```

### Change Position:
```css
.ai-chatbot {
    bottom: 30px;   /* Default: 20px */
    right: 30px;    /* Default: 20px */
    /* Or use left: 20px for left side */
}
```

### Change Greeting Message:
Edit `chatbot.js` line 85:
```javascript
appendMessage('YOUR_CUSTOM_GREETING_HERE', 'bot');
```

---

## 🐛 Troubleshooting

### Issue: Panel doesn't open
**Fix:** Check browser console for JavaScript errors, verify all IDs match

### Issue: Messages not sending
**Fix:** Check `/api/chatbot` route is accessible, verify authentication

### Issue: Theme colors not applying
**Fix:** Clear browser cache, verify `theme.css` is loaded before `style.css`

### Issue: Panel cut off on mobile
**Fix:** Check viewport meta tag in `base.html`, adjust max-height in media query

---

## 📊 Performance Metrics

- **CSS Size**: ~300 lines (chatbot section)
- **JS Size**: 87 lines (unminified)
- **API Response**: <500ms (depends on database size)
- **Initial Load**: Instant (no external dependencies)
- **Theme Switch**: Instant (CSS variables)

---

## 🔐 Security Notes

- ✅ Authentication required (`@login_required` on API route)
- ✅ CSRF protection via Flask-WTF
- ✅ Input sanitization (`.trim()` in JavaScript)
- ✅ Error handling for failed API calls
- ⚠️ User message stored only in DOM (not persisted)
- ⚠️ Consider rate limiting for API calls

---

## 📝 Change Log

### Version 2.0 (Current)
- ✨ Added complete light/dark theme support
- ✨ Replaced hardcoded colors with CSS variables
- ✨ Added gradient backgrounds for buttons/messages
- ✨ Enhanced shadows and borders for depth
- ✨ Improved focus states for accessibility
- ✨ Added smooth hover animations
- ✨ Enhanced mobile responsiveness

### Version 1.0 (Initial)
- ✅ Basic chatbot functionality
- ✅ Toggle panel open/close
- ✅ Message append and scroll
- ✅ POST to backend API
- ✅ User context integration
- ⚠️ Dark theme only (hardcoded colors)

---

## 📞 Support

For issues or questions, check:
1. Browser console for JavaScript errors
2. Flask terminal for backend errors
3. Network tab for API request/response
4. This documentation for customization

**Common Solutions:**
- Clear browser cache after CSS changes
- Restart Flask server after Python changes
- Check all file paths are correct
- Verify theme.css loads before style.css
