# ECEFC Money Manager - API Routes Documentation

## Authentication Routes (`/auth`)

### Register
- **URL**: `/register`
- **Method**: `GET`, `POST`
- **Description**: User registration
- **Form Fields**: username, email, password, confirm_password

### Login
- **URL**: `/login`
- **Method**: `GET`, `POST`
- **Description**: User login
- **Form Fields**: username, password

### Logout
- **URL**: `/logout`
- **Method**: `GET`
- **Description**: User logout

---

## Personal Expense Routes (`/personal`)

### View Personal Expenses
- **URL**: `/personal`
- **Method**: `GET`
- **Auth**: Required
- **Description**: Display all personal expenses with statistics

### Add Personal Expense
- **URL**: `/personal/add`
- **Method**: `POST`
- **Auth**: Required
- **Form Fields**: title, amount, category, description, date

### Update Personal Expense
- **URL**: `/personal/update/<expense_id>`
- **Method**: `POST`
- **Auth**: Required
- **Form Fields**: title, amount, category, description, date

### Delete Personal Expense
- **URL**: `/personal/delete/<expense_id>`
- **Method**: `POST`
- **Auth**: Required

### Get Personal Stats (API)
- **URL**: `/personal/stats`
- **Method**: `GET`
- **Auth**: Required
- **Returns**: JSON with total, count, and category breakdown

---

## Group Expense Routes (`/group`)

### View Groups
- **URL**: `/group`
- **Method**: `GET`
- **Auth**: Required
- **Description**: List all groups user is member of

### Create Group
- **URL**: `/group/create`
- **Method**: `POST`
- **Auth**: Required
- **Form Fields**: name, description

### View Group Detail
- **URL**: `/group/<group_id>`
- **Method**: `GET`
- **Auth**: Required
- **Description**: View group expenses, members, and balances

### Add Group Expense
- **URL**: `/group/<group_id>/add_expense`
- **Method**: `POST`
- **Auth**: Required
- **Form Fields**: title, amount, description, date, split_type

### Add Group Member
- **URL**: `/group/<group_id>/add_member`
- **Method**: `POST`
- **Auth**: Required (must be group creator)
- **Form Fields**: username

### Settle Expense
- **URL**: `/group/<group_id>/settle/<expense_id>`
- **Method**: `POST`
- **Auth**: Required
- **Description**: Mark user's share as paid

---

## Tuition Routes (`/tuition`)

### View Tuition Records
- **URL**: `/tuition`
- **Method**: `GET`
- **Auth**: Required
- **Description**: Display all tuition records with statistics

### Add Tuition Record
- **URL**: `/tuition/add`
- **Method**: `POST`
- **Auth**: Required
- **Form Fields**: semester, amount, due_date, notes

### Update Tuition Record
- **URL**: `/tuition/update/<record_id>`
- **Method**: `POST`
- **Auth**: Required
- **Form Fields**: semester, amount, paid_amount, due_date, status, notes

### Make Payment
- **URL**: `/tuition/pay/<record_id>`
- **Method**: `POST`
- **Auth**: Required
- **Form Fields**: payment_amount

### Delete Tuition Record
- **URL**: `/tuition/delete/<record_id>`
- **Method**: `POST`
- **Auth**: Required

### Get Tuition Stats (API)
- **URL**: `/tuition/stats`
- **Method**: `GET`
- **Auth**: Required
- **Returns**: JSON with totals and status counts

---

## Database Schema

### Users
- id, username, email, password, created_at

### Personal Expenses
- id, user_id, title, amount, category, description, date, created_at

### Groups
- id, name, description, created_by, created_at

### Group Members
- id, group_id, user_id, joined_at

### Group Expenses
- id, group_id, paid_by, title, amount, description, date, created_at

### Expense Splits
- id, expense_id, user_id, share_amount, is_paid

### Tuition Records
- id, user_id, semester, amount, paid_amount, due_date, status, notes, created_at
