# Group Real-Time Updates - FinBuddy

## Overview

When a user views a group page, they are now connected to a **WebSocket room** for that specific group. Any changes made by group members (adding expenses, updating settlements) instantly broadcast to all other members viewing that group.

## Features

### ✅ Real-Time Group Updates

1. **Automatic Group Room Joining**
   - Users automatically join a group-specific WebSocket room when viewing group details
   - Leave the room when navigating away from group page

2. **Instant Expense Broadcasting**
   - When a member adds an expense, ALL members in the group receive instant update
   - No refresh needed - data appears automatically

3. **Live Member Contributions**
   - Member payment totals update in real-time
   - Balance calculations reflect new expenses instantly
   - Contribution bars animate smoothly

4. **Settlement Updates**
   - Calculated settlements refresh automatically
   - Shows who owes whom with latest balances
   - Updates when debts are settled

5. **Group History**
   - New expenses appear at top of group history
   - Old entries animate smoothly
   - No duplicate entries

## Technical Architecture

### WebSocket Events

**Backend Events (`app.py`):**
```python
@socketio.on('join_group')         # User joins group room
@socketio.on('leave_group')        # User leaves group room
@socketio.on('request_group_update') # Request group data refresh
```

**Broadcasting Functions:**
```python
broadcast_group_expense_update(group_id, expense_data)
  - Sends to all members in group_{group_id} room
  - Also sends to each member's personal user_{user_id} room
  - Includes full recalculated group data
```

**Frontend Events (`static/js/realtime.js`):**
```javascript
socket.on('group_updated')         // Receive group data update
socket.on('group_expense_added')   // Expense added notification
socket.on('user_viewing_group')    // User joined group room
joinGroupRoom(groupId)             // Join group room
leaveGroupRoom(groupId)            // Leave group room
```

### Data Flow

**When User Adds Group Expense:**
1. User submits form
2. Backend saves expense to database
3. `broadcast_group_expense_update()` called
4. All group members receive `group_updated` event
5. Frontend updates:
   - Member contributions
   - Total spent
   - Fair share
   - Settlements needed
   - Group history list
6. All updates animate smoothly with visual feedback

### Template Integration

**Group Details Template (`templates/groupDetails.html`):**
```html
<!-- Page container marks the group ID -->
<div data-group-id="{{ group.id }}">

<!-- Real-time updatable sections -->
<p data-field="total-expense">৳{{ total_group_expense }}</p>
<p data-field="fair-share">৳{{ fair_share }}</p>

<!-- Lists updated with fresh data -->
<div data-field="members-list">...members...</div>
<div data-field="expenses-list">...expenses...</div>
<div data-field="settlements">...settlements...</div>

<!-- Auto-join and leave group room -->
<script>
  joinGroupRoom(groupId);
  window.addEventListener('beforeunload', () => leaveGroupRoom(groupId));
</script>
```

## Usage Flow

### For Users Viewing Group Page

1. **Page Load**
   - User navigates to `/groups/<id>`
   - JavaScript detects group ID from `data-group-id` attribute
   - Automatically joins `group_{group_id}` WebSocket room
   - Requests initial group data

2. **While Viewing**
   - Auto-refresh every 25 seconds (as fallback)
   - Instant updates when other members add expenses
   - Toast notifications appear for new expenses
   - "User viewing group" broadcast sent to other members

3. **Page Leave**
   - `beforeunload` event triggered
   - JavaScript calls `leaveGroupRoom()`
   - User removed from group's WebSocket room

### For Multiple Members in Same Group

**Scenario:** Alice and Bob are both viewing Group "Apartment"

1. Alice adds expense: "$100 for groceries"
2. Backend processes and broadcasts
3. Bob's page **instantly updates** without refresh:
   - Total spent increases
   - Alice's contribution bar grows
   - New expense appears in history
   - Settlements recalculate
   - Animation plays on all updated values

4. Bob gets toast notification: "New expense added by alice!"

## Room Architecture

```
Socket.IO Rooms:
├── user_{user_id}              (Personal updates)
│   ├── Dashboard updates
│   ├── Personal expenses
│   └── Group notifications
│
├── group_{group_id}            (Group-specific)
│   ├── All members in this group
│   ├── Real-time expense updates
│   ├── Settlement calculations
│   └── Member contribution changes
```

**Benefits:**
- Only relevant users receive updates
- No broadcast storms
- Scalable to many groups
- Private data stays private

## API Endpoints

### WebSocket Events

| Event | Direction | Payload | Response |
|-------|-----------|---------|----------|
| `join_group` | C→S | `{group_id}` | true/false |
| `leave_group` | C→S | `{group_id}` | true/false |
| `request_group_update` | C→S | `{group_id}` | emits `group_updated` |
| `group_updated` | S→C | Full group data | - |
| `group_expense_added` | S→C | Expense + group_id | - |
| `user_viewing_group` | S→C | `{user_id, username}` | - |

### Group Data Structure

```javascript
{
  id: 5,
  name: "Apartment",
  total_expense: 500.00,
  fair_share: 100.00,
  member_count: 5,
  members: [
    {
      id: 1,
      username: "alice",
      total_paid: 150.00,
      expense_count: 2,
      balance: 50.00
    },
    ...
  ],
  expenses: [
    {
      id: 10,
      title: "Groceries",
      amount: 100.00,
      paid_by: 1,
      date: "2025-12-27"
    },
    ...
  ],
  settlements: [
    {
      from: "bob",
      to: "alice",
      amount: 25.00
    },
    ...
  ]
}
```

## Performance Optimizations

### 1. Room-Based Broadcasting
- Only members of group receive updates
- No database queries for non-group users
- Scales to thousands of concurrent users

### 2. Throttled Auto-Refresh
- Auto-update every 25 seconds (fallback)
- Instant updates on changes
- Prevents excessive database queries

### 3. Efficient Data Updates
- Only changed elements update in DOM
- Animations on updates only
- No full page refresh

### 4. Smart Member Notifications
- Sends to both room + personal rooms
- Ensures delivery even if user not in group room
- Redundancy for reliability

## Error Handling

### Connection Failures
```javascript
socket.on('disconnect', function() {
    // Auto-reconnect triggered
    // Shows "Disconnected" toast
    // Stops sending updates
    // Resumes when reconnected
});
```

### Failed Group Joins
```python
@socketio.on('join_group')
def handle_join_group(data):
    # Verify user is group member
    # Return False if not member
    # Prevents unauthorized access
```

### Broadcast Failures
```python
try:
    broadcast_group_expense_update(group_id, data)
except Exception as e:
    print(f"Broadcast error: {e}")
    # Application continues
    # User can manually refresh if needed
```

## Configuration

### Update Interval

In `static/js/realtime.js`:
```javascript
// Request group update every 25 seconds
setInterval(() => {
    const groupId = document.querySelector('[data-group-id]')?.getAttribute('data-group-id');
    if (groupId) {
        requestGroupUpdate(groupId);
    }
}, 25000);  // Change this value
```

### Auto-Join/Leave

Currently enabled by default in `templates/groupDetails.html`:
```html
<script>
    // Auto-join on load
    joinGroupRoom(parseInt(groupId));
    
    // Auto-leave on unload
    window.addEventListener('beforeunload', () => leaveGroupRoom(groupId));
</script>
```

To disable: Comment out the script block or remove the events.

## Testing

### Test Real-Time Updates

1. **Open Two Browser Windows**
   - Window A: Group 1 on Computer 1
   - Window B: Same Group 1 on Computer 2
   - Both logged in as different users

2. **Add Expense in Window A**
   - Form submits
   - Window B updates **instantly**
   - No refresh needed

3. **Check Console**
   ```javascript
   // Both windows should show:
   "Group update received: {data...}"
   "User viewing group: {username...}"
   ```

4. **Verify Data Accuracy**
   - Totals match between windows
   - Member contributions correct
   - Settlements recalculated properly

### Test Room Management

1. **Join Group Page**
   - Console shows: "Joined group room: 5"

2. **Navigate Away**
   - Console shows: "Left group room: 5"
   - Stops receiving updates

3. **Return to Group**
   - Console shows: "Joined group room: 5"
   - Resumes receiving updates

## Troubleshooting

### Updates Not Appearing

1. Check browser console for errors
2. Verify WebSocket connected: `socket.connected`
3. Confirm group ID found: `document.querySelector('[data-group-id]')`
4. Check server logs for broadcast errors

### Notifications Appearing Late

1. Check network latency
2. Verify no browser extensions blocking WebSocket
3. Try in incognito mode
4. Check server CPU/memory usage

### Same Expense Appearing Twice

1. Clear browser cache
2. Check for duplicate expense records in database
3. Verify broadcast called only once
4. Check for redirect causing duplicate request

## Future Enhancements

### Planned Features

1. **Live User Count**
   - Show "3 members viewing this group"
   - Real-time avatars of viewing users

2. **Typing Indicators**
   - See when another member is adding expense
   - "alice is adding an expense..."

3. **Expense Reactions**
   - React to expenses with emoji
   - "alice reacted with 🤦 to your expense"

4. **Activity Timeline**
   - "Bob added $50 expense - 2 minutes ago"
   - Real-time activity feed

5. **Conflict Resolution**
   - Handle simultaneous edits
   - "You and Alice are editing this group"

## FAQ

**Q: What if internet disconnects?**
A: Socket.IO automatically reconnects. Users will see latest data on reconnect.

**Q: Can users see private expenses?**
A: Only group members in the group room receive updates. Private data stays private.

**Q: Does it work on mobile?**
A: Yes! WebSocket is fully supported on mobile browsers.

**Q: What about old browsers?**
A: Socket.IO automatically falls back to long-polling if WebSocket unavailable.

**Q: How many groups can I join?**
A: Unlimited! Each group gets its own room. You can join/leave as needed.

**Q: Do expenses auto-save without group?**
A: Yes, expenses save immediately. WebSocket only adds real-time notifications.
