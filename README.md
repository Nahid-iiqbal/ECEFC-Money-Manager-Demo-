# ECEFC Money Manager

An expense tracker specially made for BUET students to manage personal expenses, group expenses, and tuition fees.

## Features

- 👤 **User Authentication**: Secure registration and login system
- 💰 **Personal Expense Tracking**: Track your daily expenses by category
- 👥 **Group Expenses**: Split bills and track shared expenses with friends
- 🎓 **Tuition Management**: Keep track of tuition fees and payment status
- 📊 **Statistics & Analytics**: View spending patterns and financial summaries

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Werkzeug password hashing

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd ECEFC-Money-Manager-Demo-
```

2. **Run setup script** (Windows)
```bash
setup.bat
```

Or manually:

3. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env and set your SECRET_KEY
```

6. **Initialize database**
```bash
python database.py
```

7. **Run the application**
```bash
python app.py
```

8. **Access the application**
Open your browser and go to: `http://localhost:5000`

## Project Structure

```
ECEFC-Money-Manager-Demo-/
├── app.py                  # Main Flask application
├── database.py             # Database setup and models
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── routes/
│   ├── __init__.py        # Blueprint registration
│   ├── auth.py            # Authentication routes
│   ├── personal_expense.py # Personal expense routes
│   ├── group.py           # Group expense routes
│   └── tuition_app.py     # Tuition management routes
├── templates/             # HTML templates
│   ├── index.html
│   ├── auth.html
│   ├── personal.html
│   ├── group.html
│   └── tuition.html
└── static/               # CSS and JavaScript files
    ├── css/
    └── js/
```

## API Routes

See [API_ROUTES.md](API_ROUTES.md) for complete API documentation.

## Usage

### Personal Expenses
1. Login to your account
2. Navigate to Personal Expenses
3. Add expenses with title, amount, category, and date
4. View statistics and spending patterns

### Group Expenses
1. Create a group or join existing one
2. Add expenses and they'll be split equally among members
3. Track who paid and who owes money
4. Settle expenses when paid

### Tuition Management
1. Add tuition records with semester and due date
2. Make partial or full payments
3. Track pending, partial, and paid status
4. View total dues and payment history

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Security Notes

⚠️ **Important**: 
- Change the `SECRET_KEY` in `.env` before deploying to production
- Never commit the `.env` file to version control
- Use strong passwords for user accounts
- Consider using HTTPS in production

## License

This project is for educational purposes for BUET students.

## Contributors

Made with ❤️ for BUET community
