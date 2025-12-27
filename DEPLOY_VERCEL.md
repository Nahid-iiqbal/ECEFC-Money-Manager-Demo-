# Deploying FinBuddy to Vercel

This guide explains how to deploy FinBuddy to Vercel's serverless platform.

## ⚠️ Important Limitations

When deployed on Vercel, the following features will be **disabled** due to serverless constraints:

1. **Real-time Updates (WebSocket/SocketIO)** - Dashboard and group updates won't happen in real-time. Users must manually refresh.
2. ~~**Background Email Reminders (APScheduler)**~~ - **✅ NOW WORKS!** Email reminders are handled by Vercel Cron Jobs (runs daily at 9:00 AM UTC).
3. **SQLite Database** - Vercel's filesystem is ephemeral. You **must** use an external database.

These features work normally in local development.

## Prerequisites

1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional) - Install with `npm install -g vercel`
3. **External Database** - Required for production (see Database Setup below)

## Database Setup

SQLite won't work on Vercel. Choose one of these options:

### Option A: PostgreSQL (Recommended)

Use a hosted PostgreSQL service:
- [Neon](https://neon.tech) - Free tier available
- [Supabase](https://supabase.com) - Free tier available
- [Railway](https://railway.app) - Free tier available
- [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres) - Paid

Get your connection string in this format:
```
postgresql://username:password@host:port/database
```

### Option B: MySQL

Use a hosted MySQL service:
- [PlanetScale](https://planetscale.com) - Free tier available
- [Railway](https://railway.app) - Free tier available

Connection string format:
```
mysql://username:password@host:port/database
```

### Option C: Demo Mode (Not Recommended)

For testing only, you can use SQLite knowing that data will be lost between deployments:
```
sqlite:///database.db
```

## Required Environment Variables

Configure these in your Vercel project settings:

### 🔴 REQUIRED

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret (generate a strong random string) | `your-super-secret-key-here` |
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host:5432/db` |

Generate a strong SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 📧 Email Features (Optional)

If you want email notifications (login alerts, etc.):

| Variable | Description | Example |
|----------|-------------|---------|
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Use TLS | `true` |
| `MAIL_USE_SSL` | Use SSL | `false` |
| `MAIL_USERNAME` | SMTP username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | SMTP password/app password | `your-app-password` |
| `MAIL_DEFAULT_SENDER` | Default sender email | `noreply@finbuddy.com` |

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833?hl=en), not your regular password.

### 🤖 AI Chatbot (Optional)

If you have AI chatbot features enabled:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for AI features |

## Deployment Methods

### Method 1: Deploy via Vercel CLI

1. Navigate to your project directory:
```bash
cd d:\OneDrive\Documents\ECEFC-Money-Manager-Demo-
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
vercel --prod
```

4. Set environment variables:
```bash
vercel env add SECRET_KEY
vercel env add DATABASE_URL
# Add other variables as needed
```

5. Redeploy after setting variables:
```bash
vercel --prod
```

### Method 2: Deploy via GitHub Integration (Recommended)

1. **Push to GitHub**:
   - Create a new repository on GitHub
   - Push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Vercel deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Vercel will auto-detect the Flask project

3. **Configure Environment Variables**:
   - In Vercel dashboard → Your Project → Settings → Environment Variables
   - Add all required variables from the table above
   - Click "Save"

4. **Deploy**:
   - Vercel will automatically deploy on push to `main` branch
   - Or click "Deploy" in the Vercel dashboard

## Post-Deployment

### Initialize Database

After first deployment, initialize your database:

1. Go to your Vercel deployment URL: `https://your-app.vercel.app`
2. The app will automatically create tables on first run (SQLAlchemy `create_all()`)
3. Register a new user to test

Alternatively, run migrations locally with your production DATABASE_URL:
```bash
# Set your production DATABASE_URL temporarily
$env:DATABASE_URL = "postgresql://user:pass@host:5432/db"
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Verify Deployment

1. Visit your Vercel URL
2. Try registering and logging in
3. Test adding expenses with reminder dates
4. **Email reminders**: Add an expense with a reminder date set to tomorrow, and it will be emailed at 9:00 AM UTC
5. **Cron job logs**: Check Vercel Dashboard → Your Project → Logs → Filter by "cron" to see reminder execution logs
6. Note: Real-time dashboard updates won't work (serverless limitation - manual refresh required)

## Troubleshooting

### Import Errors

If you get import errors, ensure all dependencies are in `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### Database Connection Errors

- Verify `DATABASE_URL` is set correctly in Vercel
- Check that your database allows connections from Vercel's IP ranges
- For PostgreSQL, ensure SSL is configured: `?sslmode=require`

### Static Files Not Loading

Vercel automatically serves files from `/static/` and `/templates/`. If assets don't load:
- Check that files exist in the correct directories
- Verify URLs in templates use `url_for('static', filename='...')`

### 500 Internal Server Error

Check Vercel logs:
- Go to Vercel Dashboard → Your Project → Logs
- Look for Python errors and stack traces

## Local Development vs Production

Your local development environment (`python app.py`) will run with:
✅ SocketIO real-time updates
✅ APScheduler background tasks
✅ SQLite database (if configured)

Your Vercel production environment will run with:
❌ No SocketIO (manual refresh required)
❌ No APScheduler (no automatic emails)
✅ External database (PostgreSQL/MySQL)

The app automatically detects the environment via the `VERCEL_DEPLOYMENT` environment variable.

## Updating Your Deployment

### Via GitHub (Automatic)
Push changes to `main` branch:
```bash
git add .
git commit -m "Your changes"
git push
```
Vercel deploys automatically.

### Via CLI
```bash
vercel --prod
```

## Cost Considerations

- **Vercel**: Free tier includes 100GB bandwidth/month
- **Neon/Supabase Postgres**: Free tier available (limited storage)
- **Email (Gmail)**: Free for personal use
- **Groq API**: Check current pricing

## Getting Help

- **Vercel Docs**: https://vercel.com/docs
- **Flask on Vercel**: https://vercel.com/guides/using-flask-with-vercel
- **Database Migrations**: Consider using Alembic for schema changes

---

**Note**: For enterprise use with real-time features and scheduled tasks, consider deploying to:
- [Railway](https://railway.app) - Supports WebSockets and background workers
- [Render](https://render.com) - Supports persistent connections
- [Fly.io](https://fly.io) - Full VM deployment
- Traditional VPS (DigitalOcean, AWS EC2, etc.)
