# Reminder System Implementation Guide

## Overview
This document explains the new reminder system for bills and dues in the FeinBuddy Money Manager application.

## New Features

### 1. Monthly Bill Category
- Added "📅 Monthly Bill" as a new expense category option
- Appears alongside existing categories in the add expense form
- Specifically designed for recurring monthly bills

### 2. Visual Category Enhancements
- **Dues**: Now displays with ⏰ emoji for better visual identification
- **Owes**: Now displays with 💳 emoji for better visual identification
- Makes it easier to quickly identify payment-related categories

### 3. Conditional Reminder Fields
- Reminder fields automatically appear when selecting these categories:
  - Bills
  - Monthly Bill
  - Dues
  - Owes
- Fields are hidden for other categories to keep the interface clean
- Includes:
  - **Reminder Date/Time**: Choose when to receive the reminder
  - **Reminder Note**: Optional note to include in the reminder email

### 4. Email Reminder System
- Automated email reminders sent at the specified date/time
- Beautiful HTML-formatted emails with:
  - Expense name and category
  - Amount due
  - Description and custom note
  - Professional gradient design matching app theme
- Uses Flask-Mail with configurable SMTP settings
- Background scheduler checks for due reminders every 15 minutes

## Technical Implementation

### Database Changes
Added three new columns to the `expense` table:
- `reminder_at` (DATETIME): When to send the reminder
- `reminder_sent` (BOOLEAN): Tracks if reminder was sent
- `reminder_note` (TEXT): Optional custom message

### Email Configuration
Required environment variables in `.env` file:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Note for Gmail users:**
- Enable 2-factor authentication on your Google account
- Generate an "App Password" for this application
- Use the app password (not your regular password) in MAIL_PASSWORD

### Background Scheduler
- Uses APScheduler with Flask integration
- Runs automatic check every 15 minutes for due reminders
- Schedules individual reminders when expenses are created
- Handles timezone-aware datetime comparisons

## Setup Instructions

### 1. Run Database Migration
Before using the new features, run the migration script:
```bash
python migrate_add_reminders.py
```

This adds the necessary columns to your existing database.

### 2. Configure Email Settings
Add your email credentials to the `.env` file (see above).

### 3. Restart Application
Restart the Flask application to load the new configuration:
```bash
python app.py
```

## Usage Instructions

### Adding an Expense with Reminder

1. **Navigate to Add Expense**
   - Go to the "Add Expense" page

2. **Select a Reminder-Enabled Category**
   - Choose one of: Bills, Monthly Bill, Dues, or Owes
   - Reminder fields will automatically appear

3. **Set Reminder Details**
   - **Reminder Date/Time**: Select when you want to be reminded
   - **Reminder Note** (optional): Add a custom message
   - Example note: "Due date is 15th, don't forget!"

4. **Complete the Form**
   - Fill in expense name, amount, etc.
   - Submit the form

5. **Confirmation**
   - You'll see a success message with the reminder time
   - The reminder is now scheduled

### Reminder Email Contents
The email you receive will include:
- Subject: "Reminder: [Category] - [Expense Name]"
- Formatted expense details
- Amount prominently displayed
- Your custom note (if provided)
- Professional styling matching the app

## Features by Category

| Category | Reminder Available | Emoji | Use Case |
|----------|-------------------|-------|----------|
| Food | ❌ | - | Daily meals, groceries |
| Transport | ❌ | - | Gas, public transit |
| Entertainment | ❌ | - | Movies, events |
| Shopping | ❌ | - | General purchases |
| **Bills** | ✅ | - | Utility bills, subscriptions |
| **Monthly Bill** | ✅ | 📅 | Recurring monthly payments |
| Health | ❌ | - | Medical expenses |
| Education | ❌ | - | School fees, books |
| **Dues** | ✅ | ⏰ | Payments owed by others |
| **Owes** | ✅ | 💳 | Money you owe |
| Other | ❌ | - | Miscellaneous |

## Troubleshooting

### Emails Not Sending
1. **Check Environment Variables**
   - Verify `.env` file has all MAIL_* variables
   - Ensure no extra spaces in values

2. **Gmail App Password**
   - Regular Gmail password won't work
   - Must use App Password with 2FA enabled

3. **Check Scheduler**
   - Verify scheduler is running in app logs
   - Look for "APScheduler" startup messages

4. **Test Email Configuration**
   ```python
   # Run this in Python console to test
   from flask_mail import Message
   from app import app, mail
   
   with app.app_context():
       msg = Message('Test', recipients=['test@example.com'], body='Test')
       mail.send(msg)
   ```

### Reminders Not Triggering
1. **Check Reminder Time**
   - Must be in the future when created
   - Uses UTC timezone internally

2. **Verify Database**
   - Check that `reminder_at` is set in database
   - Verify `reminder_sent` is False

3. **Scheduler Running**
   - Application must be running for reminders to send
   - Consider using a process manager for production

### Migration Issues
If migration fails:
```bash
# Manually add columns using SQLite
sqlite3 instance/feinbuddy.db
ALTER TABLE expense ADD COLUMN reminder_at DATETIME;
ALTER TABLE expense ADD COLUMN reminder_sent BOOLEAN DEFAULT 0 NOT NULL;
ALTER TABLE expense ADD COLUMN reminder_note TEXT;
```

## Security Notes

1. **Never commit `.env` file**
   - Already in `.gitignore`
   - Contains sensitive email credentials

2. **Use App Passwords**
   - Don't use your actual email password
   - Limit permissions to just sending email

3. **SMTP Over TLS**
   - Default configuration uses encrypted connection
   - Port 587 with TLS enabled

## Future Enhancements
Potential improvements for future versions:
- Recurring reminders for monthly bills
- SMS notification option
- Configurable reminder advance time
- Multiple reminders per expense
- Reminder history log
- Snooze/reschedule functionality

## Code Structure

### Modified Files
1. **routes/database.py** - Added reminder columns to Expense model
2. **templates/addExpense.html** - Added conditional reminder UI with JavaScript
3. **routes/expense.py** - Updated add_expense() to handle reminders
4. **app.py** - Added email functions and scheduler jobs

### New Files
1. **migrate_add_reminders.py** - Database migration script

## Support
For issues or questions:
1. Check this README
2. Review error logs in terminal
3. Verify environment configuration
4. Test with a simple expense first

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Compatible With**: FeinBuddy Money Manager v1.0+
