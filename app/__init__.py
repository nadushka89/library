from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from flask_login import LoginManager

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Конфигурация базы данных

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  #  куда пользователь будет перенаправлен, если он не авторизован

from . import routes
from .models import User 
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

