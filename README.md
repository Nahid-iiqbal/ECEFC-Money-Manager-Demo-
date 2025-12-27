
A comprehensive personal finance management web application built for BUET students. Track expenses, manage tuition income, split bills with friends, and get AI-powered financial insights.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.2-green)
![License](https://img.shields.io/badge/License-Educational-orange)


## ✨ Features

### 💳 Personal Expense Tracking

### 👥 Group Expenses & Bill Splitting

### 🎓 Tuition Management

### 📊 Dashboard & Analytics

### 🤖 AI-Powered Chatbot (FinBuddy Assistant)

### 📧 Email Notifications

### 🔐 User Profiles

### ⚡ Real-time Features

# 💰 FinBuddy
---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Flask 3.1.2, Flask-SQLAlchemy, Flask-Login |
| **Real-time** | Flask-SocketIO, Flask-APScheduler |
| **AI/ML** | Groq API (Mixtral-8x7b-32768) |

## 📁 Project Structure

```
ECEFC-Money-Manager-Demo-/
├── app.py                      # Main Flask application
├── database.py                 # Database initialization script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
│
├── routes/                    # Route blueprints
│   ├── auth.py               # Authentication (login/register)
│   ├── dashboard.py          # Dashboard views
│   ├── expense.py            # Personal expense management
│   ├── group.py              # Group expense management
│   ├── tuition.py            # Tuition tracking & PDF export
│   ├── profile.py            # User profile management
│
├── services/                  # Business logic services
│   └── chat_context.py       # RAG-style chatbot context builder
│
├── tools/                     # CLI utilities
│   └── export_anonymized_analytics.py  # Analytics export (no PII)
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html             # Base layout template
│   ├── landing.html          # Landing page
│   ├── auth_new.html         # Login/Register page
│   ├── dashboard.html        # Main dashboard
│   ├── personal.html         # Personal expenses view
│   ├── groupDetails.html     # Group details & balances
│   ├── tuition.html          # Tuition management
│   ├── profile_*.html        # Profile pages
│   └── email_*.html          # Email templates
│
├── static/                    # Static assets
│   ├── css/                  # Stylesheets
│   │   ├── theme.css        # Global theme & variables
│   │   ├── dashboard.css    # Dashboard styles
│   │   └── ...
├── instance/                  # Instance-specific files
│   └── finance.db            # SQLite database (local)
```

- PostgreSQL (for production) or SQLite (for development)

### Quick Start (Windows)

```bash
# Clone the repository
git clone https://github.com/Nahid-iiqbal/ECEFC-Money-Manager-Demo-.git
cd ECEFC-Money-Manager-Demo-

# Run setup script
setup.bat
```

### Manual Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your settings:
   ```env
   SECRET_KEY=your-secret-key-here
   
   # Database (leave empty for SQLite)
   DATABASE_URL=postgresql://user:pass@host/db
   
   # Email configuration
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   
   # AI Chatbot (optional)
   GROQ_API_KEY=your-groq-api-key
   GROQ_MODEL_NAME=mixtral-8x7b-32768
   
   # Feature flags
   ENABLE_WEEKLY_REPORTS=true
   ENABLE_TUITION_REMINDERS=true
   ```

4. **Initialize database**
   ```bash
   python database.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   
   Open: `http://localhost:5000`

---

## 📖 API Documentation

See [API_ROUTES.md](API_ROUTES.md) for complete API documentation including:
- Authentication endpoints
- Personal expense CRUD operations
- Group management APIs
- Tuition tracking endpoints
- Statistics and analytics APIs

---

## 🎯 Usage Guide

### Personal Expenses
1. Navigate to **Personal Expenses** from the dashboard
2. Click **Add Expense** to log a new expense
3. Select category, enter amount and description
4. View spending statistics and trends

### Group Expenses
1. Create a new group or join with a code
2. Add expenses and split among members
3. Track balances - who owes whom
4. Mark expenses as settled when paid

### Tuition Management
1. Add tuition records with student details
2. Set scheduled days and class times
3. Track class completion progress
4. Reschedule classes when needed
5. Export PDF reports for records

### AI Chatbot
1. Click the chat icon on the dashboard
2. Ask questions like:
   - "What's my spending this week?"
   - "Which category do I spend most on?"
   - "How can I save more money?"

---

## 🔧 Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Required |
| `DATABASE_URL` | PostgreSQL connection string | SQLite |
| `GROQ_API_KEY` | Groq API key for chatbot | Optional |
| `ENABLE_WEEKLY_REPORTS` | Send weekly email reports | `true` |
| `ENABLE_TUITION_REMINDERS` | Send tuition reminders | `true` |
| `WEEKLY_REPORT_DAY` | Day for weekly reports | `sun` |
| `WEEKLY_REPORT_HOUR` | Hour for weekly reports | `8` |

---

## 🛡️ Security Notes

⚠️ **Important for Production**:
- Change `SECRET_KEY` to a strong random value
- Never commit `.env` to version control
- Use HTTPS in production
- Configure proper CORS settings
- Use strong passwords for user accounts
- PostgreSQL recommended for production

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational purposes for BUET students.

---

## 💖 Contributors

Made with ❤️ for the BUET community

---

## 📞 Support

For issues or feature requests, please open a GitHub issue.
