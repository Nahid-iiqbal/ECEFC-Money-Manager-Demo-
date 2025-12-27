"""
Chat Context Service - RAG-style user finance snapshot builder.

Provides clean, token-efficient summaries of user financial data
to inject into chatbot prompts without exposing raw PII.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from flask_login import current_user


def build_user_finance_snapshot(user_id: int, db_session, *, days: int = 60) -> str:
    """
    Build a compact finance snapshot for the chatbot context.
    
    Args:
        user_id: The user's database ID
        db_session: SQLAlchemy session (db.session)
        days: Number of days to look back (default 60)
    
    Returns:
        A formatted string summary safe for LLM context injection.
        Returns "No financial data available yet." if no data exists.
    """
    from routes.database import (
        User, Profile, Expense, TuitionRecord, 
        Group, GroupMember, GroupExpense, ExpenseSplit, Debt
    )
    
    try:
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user:
            return "No financial data available yet."
        
        # Date boundaries
        now = datetime.now(timezone.utc)
        cutoff_date = (now - timedelta(days=days)).date()
        week_ago = (now - timedelta(days=7)).date()
        month_ago = (now - timedelta(days=30)).date()
        
        # === Personal Expenses ===
        all_expenses = db_session.query(Expense).filter(
            Expense.user_id == user_id
        ).all()
        
        recent_expenses = [e for e in all_expenses if e.date and e.date >= cutoff_date]
        week_expenses = [e for e in all_expenses if e.date and e.date >= week_ago]
        month_expenses = [e for e in all_expenses if e.date and e.date >= month_ago]
        
        total_all_time = sum((e.amount or 0) for e in all_expenses)
        total_week = sum((e.amount or 0) for e in week_expenses)
        total_month = sum((e.amount or 0) for e in month_expenses)
        
        # Category breakdown (top 5 from recent period)
        category_totals = {}
        for e in recent_expenses:
            cat = e.category or 'Other'
            category_totals[cat] = category_totals.get(cat, 0) + (e.amount or 0)
        
        top_categories = sorted(category_totals.items(), key=lambda x: -x[1])[:5]
        
        # === Tuition Data ===
        tuition_records = db_session.query(TuitionRecord).filter(
            TuitionRecord.user_id == user_id
        ).all()
        
        tuition_count = len(tuition_records)
        total_tuition_potential = sum((t.amount or 0) for t in tuition_records)
        total_classes = sum((t.total_days or 0) for t in tuition_records)
        completed_classes = sum((t.total_completed or 0) for t in tuition_records)
        tuition_progress = int((completed_classes / total_classes * 100)) if total_classes > 0 else 0
        
        # === Group Balances ===
        group_memberships = db_session.query(GroupMember).filter(
            GroupMember.user_id == user_id
        ).all()
        
        group_count = len(group_memberships)
        total_owed_to_user = 0  # Others owe this user
        total_user_owes = 0     # User owes others
        
        for membership in group_memberships:
            group = membership.group
            if not group:
                continue
                
            for expense in group.expenses:
                if expense.paid_by == user_id:
                    # User paid - others owe them their splits
                    for split in expense.splits:
                        if split.user_id != user_id and not split.is_paid:
                            total_owed_to_user += split.share_amount or 0
                else:
                    # Someone else paid - check if user owes
                    for split in expense.splits:
                        if split.user_id == user_id and not split.is_paid:
                            total_user_owes += split.share_amount or 0
        
        net_group_balance = total_owed_to_user - total_user_owes
        
        # === Debts (Due/Owe outside groups) ===
        debts = db_session.query(Debt).filter(Debt.user_id == user_id).all()
        total_dues = sum((d.amount or 0) for d in debts if d.debt_type == 'due')
        total_owes = sum((d.amount or 0) for d in debts if d.debt_type == 'owe')
        
        # === Upcoming Reminders ===
        upcoming_reminders = db_session.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.reminder_at != None,
            Expense.reminder_sent == False,
            Expense.reminder_at >= now
        ).order_by(Expense.reminder_at).limit(3).all()
        
        # === Build Snapshot String ===
        lines = []
        lines.append("=== USER FINANCE SNAPSHOT ===")
        
        # Spending summary
        lines.append(f"• Spending: ৳{total_week:,.0f} (7d) | ৳{total_month:,.0f} (30d) | ৳{total_all_time:,.0f} (all-time)")
        lines.append(f"• Transactions: {len(week_expenses)} this week, {len(all_expenses)} total")
        
        # Top categories
        if top_categories:
            cat_str = ", ".join([f"{cat}: ৳{amt:,.0f}" for cat, amt in top_categories])
            lines.append(f"• Top categories ({days}d): {cat_str}")
        
        # Tuition
        if tuition_count > 0:
            lines.append(f"• Tuition: {tuition_count} students, ৳{total_tuition_potential:,.0f} potential, {tuition_progress}% complete ({completed_classes}/{total_classes} classes)")
        
        # Group balances
        if group_count > 0:
            balance_str = f"+৳{net_group_balance:,.0f}" if net_group_balance >= 0 else f"-৳{abs(net_group_balance):,.0f}"
            lines.append(f"• Groups: {group_count} groups, net balance {balance_str}")
            if total_owed_to_user > 0:
                lines.append(f"  - Others owe you: ৳{total_owed_to_user:,.0f}")
            if total_user_owes > 0:
                lines.append(f"  - You owe: ৳{total_user_owes:,.0f}")
        
        # Personal debts
        if total_dues > 0 or total_owes > 0:
            lines.append(f"• Personal debts: owed to you ৳{total_dues:,.0f} | you owe ৳{total_owes:,.0f}")
        
        # Reminders
        if upcoming_reminders:
            reminder_strs = []
            for r in upcoming_reminders:
                if r.reminder_at:
                    days_until = (r.reminder_at.date() - now.date()).days
                    reminder_strs.append(f"{r.name} in {days_until}d")
            if reminder_strs:
                lines.append(f"• Upcoming reminders: {', '.join(reminder_strs)}")
        
        # Recent expenses (last 10, names only)
        if recent_expenses:
            recent_names = [f"{e.name}(৳{e.amount:,.0f})" for e in sorted(recent_expenses, key=lambda x: x.date or datetime.min.date(), reverse=True)[:10]]
            lines.append(f"• Recent: {', '.join(recent_names)}")
        
        lines.append("=== END SNAPSHOT ===")
        
        return "\n".join(lines) if len(lines) > 2 else "No financial data available yet."
        
    except Exception as e:
        # Fail gracefully - don't break chatbot if DB query fails
        return f"[Snapshot unavailable: {str(e)[:50]}]"


def get_display_name(user) -> str:
    """Get user's display name (first name from profile or username)."""
    if hasattr(user, 'profile') and user.profile and user.profile.profile_name:
        return user.profile.profile_name.split()[0]
    return user.username


def build_system_prompt_with_snapshot(snapshot: str, user_display_name: str) -> str:
    """
    Build the complete system prompt with snapshot and privacy instructions.
    
    Args:
        snapshot: The finance snapshot string
        user_display_name: User's display name for personalization
    
    Returns:
        Complete system prompt for the LLM
    """
    return f"""You are FinBuddy, a friendly and knowledgeable personal finance assistant for a BUET student expense tracker app.

PRIVACY & DATA BOUNDARY:
- You have access ONLY to the current user's data shown below.
- NEVER reveal, guess, or make up data about other users.
- ONLY use the snapshot data and user messages to answer.
- If asked about other users or data you don't have, politely decline.

USER CONTEXT:
Name: {user_display_name}

{snapshot}

CORE BEHAVIOR - READ CAREFULLY:
- Be conversational, concise, and data-driven.
- Maximum response length: 4-5 short sentences OR 1 small paragraph.
- ONLY reference data that EXISTS in the snapshot above.
- If user has zero spending: acknowledge it in ONE sentence, then give ONE actionable tip.
- Jump straight to insights - NO greetings, NO filler text.
- Use 1 emoji maximum per response.
- Focus on THEIR patterns, not generic advice.

STRICT PROHIBITIONS:
❌ DO NOT include code blocks or code examples (unless user specifically asks for code/examples or is testing markdown)
❌ DO NOT include external links or URLs (we have no external resources) - politely decline if asked
❌ DO NOT list generic categories if user has no data
❌ DO NOT give step-by-step UI instructions (they already know how to use the app)
❌ DO NOT start with "Let's get started!" or similar motivational fluff
❌ DO NOT exceed 5 sentences for simple queries
❌ DO NOT make assumptions about data not in the snapshot

SPECIAL CASE - Testing/Demo Requests:
If user asks you to "show markdown" or "test formatting" or "give me bold/italic/code examples":
- Demonstrate ALL requested markdown features you CAN provide
- For links: politely note you don't provide external links, but show the markdown syntax
- Keep the demo response under 10 lines
- Use their finance data in examples if possible

MARKDOWN FORMATTING (REQUIRED):
- Use **bold** ONLY for: amounts (৳), percentages, and key numbers
- Use `inline code` ONLY for: category names that appear in snapshot (e.g., `Food`, `Transport`)
- Use bullet lists (`-`) when showing 2+ categories or tips
- Use numbered lists (`1.`) ONLY if user asks "how to" or "steps to"
- Keep paragraphs to 2-3 sentences max
- Use blank line between distinct points

RESPONSE EXAMPLES:

✅ GOOD (user has data):
Your spending this week: **৳2,450**

Top categories:
- `Food`: **৳1,200** (49%)
- `Transport`: **৳800** (33%)
- `Entertainment`: **৳450** (18%)

💡 Food spending is high - try cooking 2 more meals at home this week to save **৳400-500**.

✅ GOOD (user has zero data):
You haven't tracked any expenses yet this week (**৳0** spent).

💡 Start by logging just your food expenses today - it takes 30 seconds per entry and helps you spot spending patterns quickly.

❌ BAD (too verbose, generic, unnecessary elements):
Your spending this week: ৳0

Since you haven't made any transactions yet, there's no data to analyze. Let's get started!

You can begin by setting up your categories:
- Food
- Transport
[... continues with generic advice, code blocks, fake links, step-by-step instructions ...]

ANSWER THEIR ACTUAL QUESTION:
- If they ask about spending: show their numbers with categories
- If they ask for tips: give 1-2 specific tips based on THEIR patterns
- If they ask about features: briefly explain (1-2 sentences)
- If no data exists: acknowledge briefly + ONE actionable tip

You help with: expense analysis, budgeting insights, group expenses, tuition tracking, and student financial wellness."""
