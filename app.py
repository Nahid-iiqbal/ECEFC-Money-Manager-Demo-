from flask import Flask, render_template
from routes.database import db, init_db, User
from routes.auth import auth_bp
from flask_login import LoginManager
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register blueprints
app.register_blueprint(auth_bp)


@app.route('/')
def home():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)
