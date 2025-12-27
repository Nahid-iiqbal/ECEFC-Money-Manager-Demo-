# Vercel Deployment Files Summary

This document summarizes the files created and modified for Vercel deployment.

## Files Created

### 1. `vercel.json`
Configuration file for Vercel deployment:
- Specifies Python runtime (3.11)
- Routes static assets to `/static/` directory
- Routes all other requests to `api/index.py` (serverless function)

### 2. `api/index.py`
Serverless function entrypoint:
- Sets `VERCEL_DEPLOYMENT=true` environment variable
- Imports Flask app from main `app.py`
- Exposes app for Vercel's WSGI handler

### 3. `.vercelignore`
Excludes unnecessary files from deployment:
- Python cache files
- Virtual environments
- `.env` files
- SQLite databases
- IDE configs

### 4. `DEPLOY_VERCEL.md`
Complete deployment guide including:
- Feature limitations on serverless
- Database setup instructions (PostgreSQL/MySQL)
- Required environment variables
- Step-by-step deployment via CLI or GitHub
- Troubleshooting tips

### 5. `VERCEL_FILES.md`
This file - quick reference of all changes.

## Files Modified

### `app.py`
Added conditional initialization logic:

1. **Imports (lines 1-20)**:
   - Added `IS_VERCEL` flag check
   - Conditionally imports SocketIO and APScheduler only for local development
   - Creates dummy variables when on Vercel

2. **SocketIO/Scheduler Init (lines ~395-408)**:
   - Wrapped in `if not IS_VERCEL:` block
   - Sets `socketio = None` and `scheduler = None` on Vercel

3. **SocketIO Event Handlers (lines ~1050-1175)**:
   - Wrapped all `@socketio.on()` decorators in `if not IS_VERCEL and socketio:` block
   - Added stub functions for Vercel to prevent import errors

4. **Main Execution (lines ~1200-1210)**:
   - Uses `app.run()` when `IS_VERCEL=true`
   - Uses `socketio.run()` for local development

## Environment Variable Detection

The app detects its environment via:
```python
IS_VERCEL = os.environ.get('VERCEL_DEPLOYMENT') == 'true'
```

This variable is automatically set by `api/index.py` before importing the app.

## Local vs Production Behavior

| Feature | Local Development | Vercel Production |
|---------|------------------|-------------------|
| SocketIO | ✅ Enabled | ❌ Disabled |
| APScheduler | ✅ Enabled | ❌ Disabled |
| Real-time Updates | ✅ Works | ❌ Manual refresh |
| Email Reminders | ✅ Scheduled | ❌ Not available |
| Database | SQLite (default) | External DB required |
| Server | `socketio.run()` | `app.run()` (WSGI) |

## Quick Deployment Checklist

- [x] Created `vercel.json`
- [x] Created `api/index.py`
- [x] Modified `app.py` for conditional features
- [x] Created `.vercelignore`
- [x] Created deployment documentation
- [ ] Set up external database (PostgreSQL/MySQL)
- [ ] Generate `SECRET_KEY`
- [ ] Configure environment variables in Vercel
- [ ] Deploy via CLI or GitHub integration

## Next Steps

1. **Set up a database**: Choose PostgreSQL (Neon, Supabase) or MySQL (PlanetScale)
2. **Generate SECRET_KEY**: Run `python -c "import secrets; print(secrets.token_hex(32))"`
3. **Deploy**: Use `vercel --prod` or connect GitHub repository
4. **Configure environment variables** in Vercel dashboard
5. **Test the deployment** at your Vercel URL

## Important Notes

- ⚠️ SQLite will NOT work on Vercel (ephemeral filesystem)
- ⚠️ Real-time features are disabled on Vercel
- ⚠️ Background tasks (email reminders) won't run on Vercel
- ✅ All other features work normally
- ✅ Local development retains full functionality

For production apps requiring WebSockets/background tasks, consider Railway, Render, or Fly.io instead.
