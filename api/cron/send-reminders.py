"""
Vercel Cron Job - Send Email Reminders
Runs daily at 9:00 AM UTC to send expense reminder emails
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Set Vercel deployment flag
os.environ['VERCEL_DEPLOYMENT'] = 'true'

from flask import jsonify
from app import app, mail
from flask_mail import Message
from routes.database import db, Expense, User


def handler(request):
    """
    Vercel Cron Job handler
    Sends email reminders for expenses due today
    """
    with app.app_context():
        try:
            # Get today's date
            today = datetime.now().date()
            
            # Find all expenses with reminders due today that haven't been sent
            expenses_to_remind = Expense.query.filter(
                Expense.reminder_date == today,
                Expense.reminder_sent == False
            ).all()
            
            sent_count = 0
            failed_count = 0
            
            for expense in expenses_to_remind:
                try:
                    # Get user and email
                    user = User.query.get(expense.user_id)
                    if not user or not user.profile or not user.profile.email:
                        continue
                    
                    email = user.profile.email
                    
                    # Create email message
                    msg = Message(
                        subject=f'Reminder: {expense.category} - {expense.name}',
                        recipients=[email],
                        html=f'''
                        <html>
                            <head>
                                <style>
                                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                              color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                                    .expense-details {{ background: white; padding: 20px; border-radius: 8px; 
                                                       margin: 20px 0; border-left: 4px solid #667eea; }}
                                    .amount {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                                </style>
                            </head>
                            <body>
                                <div class="container">
                                    <div class="header">
                                        <h1>💰 Payment Reminder</h1>
                                    </div>
                                    <div class="content">
                                        <p>Hello {user.username},</p>
                                        <p>This is a friendly reminder about your upcoming {expense.category.lower()}:</p>
                                        
                                        <div class="expense-details">
                                            <h2>{expense.name}</h2>
                                            <p><strong>Category:</strong> {expense.category}</p>
                                            <p><strong>Amount:</strong> <span class="amount">${expense.amount:.2f}</span></p>
                                            {f'<p><strong>Description:</strong> {expense.description}</p>' if expense.description else ''}
                                            <p><strong>Date:</strong> {expense.date.strftime('%B %d, %Y')}</p>
                                        </div>
                                        
                                        <p>Don't forget to make this payment on time!</p>
                                        
                                        <div class="footer">
                                            <p>This is an automated reminder from FinBuddy</p>
                                            <p>Stay on top of your finances! 💪</p>
                                        </div>
                                    </div>
                                </div>
                            </body>
                        </html>
                        '''
                    )
                    
                    # Send email
                    mail.send(msg)
                    
                    # Mark as sent
                    expense.reminder_sent = True
                    db.session.commit()
                    
                    sent_count += 1
                    
                except Exception as e:
                    print(f"Failed to send reminder for expense {expense.id}: {str(e)}")
                    failed_count += 1
                    continue
            
            return jsonify({
                'success': True,
                'message': f'Reminder cron job completed',
                'reminders_sent': sent_count,
                'failed': failed_count,
                'total_checked': len(expenses_to_remind),
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            print(f"Cron job error: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
