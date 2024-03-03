from datetime import datetime
from sqlalchemy import Date, func
from app import app

from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_login import UserMixin, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for
from app.config import api_key



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64))
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    about_me = db.Column(db.String(250))
    avatar_url = db.Column(db.String(255)) 
    book_lists = db.relationship('BookList', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='user', lazy='dynamic')  
    ratings = db.relationship('Rating', back_populates='user', lazy='dynamic')
    is_admin = db.Column(db.Boolean, default=False)
    # favorites_list = db.relationship('BookList', backref='user_favorites', uselist=False)
    # read_later_list = db.relationship('BookList', backref='user_read_later', uselist=False)
    def set_password(self, password):
        if len(password) < 7:
            return False
        self.password_hash = generate_password_hash(password)
        return True

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)



class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(120), unique=True)
    isbn = db.Column(db.String(120), unique=True)
    title = db.Column(db.String(350), nullable=False)
    author = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    page_count = db.Column(db.Integer)
    rating = db.Column(db.Float, nullable=True, default=None)
    category = db.Column(db.String(250), nullable=True)
    cover_image = db.Column(db.String(500), nullable=True)
    is_best_seller = db.Column(db.Boolean, default=False)
    published_date = db.Column(Date, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    genres = db.relationship('Genre', secondary='book_genre_association', backref='books', lazy='dynamic')
    # is_ebook = db.Column(db.Boolean, default=False)
    # web_reader_link = db.Column(db.String(500), nullable=True)  # Добавлено поле web_reader_link

    def __repr__(self):
        return f'<Book {self.title}>'

    @staticmethod
    def create_book(google_id, isbn, title, author, description, page_count, rating, category, cover_image, published_date,
                    is_best_seller=False, genres=None):
        book = Book(
            google_id=google_id, isbn=isbn, title=title, author=author, description=description, page_count=page_count,
            rating=rating, category=category, cover_image=cover_image, published_date=published_date,
            is_best_seller=is_best_seller
        )

        # Добавляем книгу в базу данных
        db.session.add(book)

        # Добавляем связи с жанрами через book_genre_association
        if genres:
            for genre in genres:
                book.genres.append(genre)

        # Вызываем commit только один раз после всех изменений
        db.session.commit()

    def calculate_average_rating(self):
        # Получаем все оценки для этой книги
        ratings = Rating.query.filter_by(book_id=self.id).all()

        # Получаем общее количество оценок
        num_ratings = len(ratings)

        # Получаем сумму всех оценок
        total_rating = sum(rating.rate for rating in ratings if rating.rate is not None)

        # Получаем оценку пользователя для этой книги
        user_rating = Rating.query.filter_by(user_id=current_user.id, book_id=self.id).first()

        # Если у пользователя есть оценка для этой книги, учитываем ее
        if user_rating and user_rating.rate is not None:
            total_rating += user_rating.rate
            num_ratings += 1

        # Если есть оценки, вычисляем средний рейтинг
        if num_ratings > 0:
            average_rating = total_rating / num_ratings
            self.rating = average_rating
        else:
            self.rating = None  # Устанавливаем рейтинг в None, если нет действительных оценок

        db.session.commit()

        return float(self.rating) if self.rating is not None else 0.0, num_ratings


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

book_genre_association = db.Table('book_genre_association',
                                 db.Column('book_id', db.Integer, db.ForeignKey('book.id'), nullable=False),
                                 db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), nullable=False),
                                 db.PrimaryKeyConstraint('book_id', 'genre_id'))

class BookList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    books = db.relationship('Book', secondary='book_list_association', backref='lists', lazy='dynamic')


book_list_association = db.Table('book_list_association',
                                 db.Column('book_id', db.Integer, db.ForeignKey('book.id'), nullable=False),
                                 db.Column('list_id', db.Integer, db.ForeignKey('book_list.id'), nullable=False),
                                 db.PrimaryKeyConstraint('book_id', 'list_id'))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user = db.relationship('User', back_populates='comments')


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    user = db.relationship('User', back_populates='ratings')



# Определяем административную модель
class AdminModelView(ModelView):
    def is_accessible(self):
        # Проверяем, является ли текущий пользователь администратором
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # Если пользователь не администратор, перенаправляем его на страницу входа
        return redirect(url_for('login'))

# Инициализируем объект администратора
admin = Admin()

# Добавляем модели, которые будут доступны в административной панели
admin.add_view(AdminModelView(User, db.session))
admin.add_view(AdminModelView(Book, db.session))
admin.add_view(AdminModelView(Genre, db.session))
admin.add_view(AdminModelView(BookList, db.session))
admin.add_view(AdminModelView(Comment, db.session))
admin.add_view(AdminModelView(Rating, db.session))

# Регистрируем администраторский объект в приложении Flask
admin.init_app(app)