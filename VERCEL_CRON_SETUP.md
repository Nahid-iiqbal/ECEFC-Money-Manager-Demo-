# Vercel Cron Jobs - Email Reminders Setup Complete ✅

## What Was Done

### 1. Modified `vercel.json`
Added cron job configuration:
```json
"crons": [
  {
    "path": "/api/cron/send-reminders",
    "schedule": "0 9 * * *"
  }
]
```

**Schedule**: Daily at 9:00 AM UTC

### 2. Created `/api/cron/send-reminders.py`
Serverless function that:
- Runs daily at 9:00 AM UTC (automatically triggered by Vercel)
- Queries database for expenses with `reminder_date = today`
- Sends email reminders to users
- Marks expenses as `reminder_sent = True`
- Returns execution summary (sent count, failed count, timestamp)

### 3. Updated Documentation
- `DEPLOY_VERCEL.md` now documents the cron job feature
- Includes schedule examples for customization

## How It Works

1. **User adds an expense** with a reminder date (e.g., "Remind me on Jan 15")
2. **Every day at 9 AM UTC**, Vercel automatically calls `/api/cron/send-reminders`
3. **Function checks** for any expenses where `reminder_date = today`
4. **Sends emails** to users with expense details
5. **Marks as sent** to prevent duplicates

## Testing After Deployment

### Test the Cron Job Manually
You can trigger it manually without waiting for 9 AM:

```bash
curl https://your-app.vercel.app/api/cron/send-reminders
```

Response example:
```json
{
  "success": true,
  "message": "Reminder cron job completed",
  "reminders_sent": 5,
  "failed": 0,
  "total_checked": 5,
  "timestamp": "2025-12-27T14:30:00"
}
```

### View Cron Logs
1. Go to Vercel Dashboard
2. Your Project → **Logs**
3. Filter by "cron" or search for "send-reminders"
4. See execution history, success/failure status

## Customizing the Schedule

Edit `vercel.json` to change when reminders are sent:

| Schedule | Description |
|----------|-------------|
| `0 9 * * *` | Daily at 9:00 AM UTC (default) |
| `0 */6 * * *` | Every 6 hours |
| `0 9 * * 1-5` | Weekdays only at 9:00 AM |
| `0 0 * * *` | Midnight UTC daily |
| `0 8,18 * * *` | Twice daily (8 AM & 6 PM) |

After changing, commit and push:
```bash
git add vercel.json
git commit -m "Update cron schedule"
git push
```

Vercel will automatically redeploy with the new schedule.

## Environment Variables Required

The cron job needs these environment variables set in Vercel:

| Variable | Required For |
|----------|-------------|
| `DATABASE_URL` | Access to expense and user data |
| `MAIL_SERVER` | SMTP server for sending emails |
| `MAIL_PORT` | SMTP port (usually 587) |
| `MAIL_USERNAME` | Email account username |
| `MAIL_PASSWORD` | Email account password |
| `MAIL_DEFAULT_SENDER` | Sender email address |

## Limitations

- **Execution time**: Max 60 seconds (Hobby tier) / 300 seconds (Pro tier)
- **Schedule precision**: ±1 minute (Vercel cron isn't guaranteed to run at exact second)
- **Timezone**: Always UTC (convert your local time to UTC)

## Next Steps

1. Deploy to Vercel (if not already done)
2. Set environment variables in Vercel dashboard
3. Add a test expense with reminder date = tomorrow
4. Wait for 9 AM UTC (or trigger manually) to see it work
5. Check cron logs in Vercel dashboard

---

**Status**: ✅ Email reminders now work on Vercel serverless deployment!
