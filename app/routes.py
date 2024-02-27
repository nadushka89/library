import os
import random
from datetime import datetime, timedelta
from app.genres_data_ru import genres_data
from werkzeug.utils import secure_filename

from dateutil import parser
import requests
from flask import render_template, request, redirect, session, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from app import app, db
from app.models import Book, User, BookList, Comment, Rating, Genre
from app.config import api_key

app.config['UPLOAD_FOLDER'] = 'static/image/avatar/'


@app.route('/')
def index():
    categories = list(genres_data.keys())
    selected_category = request.args.get('category', categories[0])
    is_homepage = True

    books_data = get_books_data_from_api(genres_data[selected_category]["name"])


    if books_data:
        all_books = [create_or_update_book(book_data) for book_data in books_data]

        bestsellers = Book.query.filter_by(is_best_seller=True).all()
        random.shuffle(bestsellers)
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=150)
        new_books = Book.query.filter(Book.published_date >= thirty_days_ago).all()
        
        random.shuffle(new_books)
        
        return render_template('index.html', bestsellers=bestsellers, genres=categories,
                               selected_category=selected_category, new_books=new_books, genres_data=genres_data,is_homepage=is_homepage)

    return 'Error: Unable to retrieve books data.'


def update_book_details(google_id):
    book = Book.query.filter_by(google_id=google_id).first()

    if not book:
        book_data = get_book_data(google_id)

        if book_data:
            book = create_or_update_book(book_data)

    return book


def get_book_data(google_id):
    url = f'https://www.googleapis.com/books/v1/volumes/{google_id}?key={api_key}&projection=full'
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get('volumeInfo')

    return None


def create_or_update_book(book_data):
    google_id = book_data.get('id')
    volume_info = book_data.get('volumeInfo', {})

    title = volume_info.get('title', 'Unknown Title')
    author = ", ".join(volume_info.get('authors', ['Unknown Author']))
    description = volume_info.get('description', '')

    # Проверяем наличие ключа 'imageLinks'
    image_links = volume_info.get('imageLinks', {})
    cover_image = image_links.get('mediumThumbnail') or image_links.get('smallThumbnail') or image_links.get(
        'thumbnail', None)

    book = Book.query.filter_by(google_id=google_id).first()
    if not book:
        book = Book(google_id=google_id, title=title, author=author,
                    description=description, cover_image=cover_image)
        add_genres_to_book(book, volume_info)

        # Добавляем обработку published_date
        try:
            published_date_str = volume_info.get('publishedDate', None)
            published_date = parser.parse(published_date_str).date() if published_date_str else None
            book.published_date = published_date
        except ValueError:
            book.published_date = None

        # Добавляем обработку pageCount
        page_count = volume_info.get('pageCount')
        book.page_count = page_count if page_count is not None else 0

        db.session.add(book)
    else:
        book.title = title
        book.author = author
        book.description = description
        book.cover_image = cover_image

        # Добавляем обработку published_date
        try:
            published_date_str = volume_info.get('publishedDate', None)
            published_date = parser.parse(published_date_str).date() if published_date_str else None
            book.published_date = published_date
        except ValueError:
            book.published_date = None

        page_count = volume_info.get('pageCount')
        book.page_count = page_count if page_count is not None else 0

    db.session.commit()

    update_book_rating(book, volume_info)
    add_genres_to_book(book, volume_info)

    return book


@app.route('/books')
def books():
    categories = list(genres_data.values())
    random_category = random.choice(categories)
    category_name = random_category.get("name")

    books_data = get_books_data_from_api(category_name)

    if books_data:
        books = [create_or_update_book(book_data) for book_data in books_data]
        random.shuffle(books)
        return render_template('books.html', books=books, genres_data=genres_data)

    return 'Error: Unable to retrieve books data.'



@app.route('/book_details/<string:google_id>')
def book_details(google_id):
    book = update_book_details(google_id)

    if book:
        # для проверки данных перед передачей в шаблон
        print(f"Page Count: {book.page_count}")
        print(f"Category/Genres: {book.category} / {book.genres}")
        print(f"Published Date: {book.published_date}")

        comments = Comment.query.filter_by(book_id=book.id).order_by(Comment.timestamp.desc()).all()
        rating = Rating.query.filter_by(book_id=book.id).all()
        cover_image = book.cover_image

        current_user_rating = None
        is_in_list = False

        if current_user.is_authenticated:
            user_rating = Rating.query.filter_by(book_id=book.id, user_id=current_user.id).first()
            if user_rating:
                current_user_rating = user_rating.rate

            user_lists = current_user.book_lists.all()
            is_in_list = any(book in user_list.books for user_list in user_lists)

        # Добавим genres_data в контекст
        return render_template('books_details.html', book=book, google_id=google_id,
                               comments=comments, cover_image=cover_image, rating=rating,
                               current_user_rating=current_user_rating, is_in_list=is_in_list,
                               genres_data=genres_data)

    return "Error: Unable to retrieve book data"

def get_books_data(keyword, start_index=None, max_results=None):
    """
    Функция для получения данных о книгах из базы данных или Google Books API.

    Args:
        keyword (str): Ключевое слово для поиска.
        start_index (int): Начальный индекс для поиска в Google Books API (необязательно).
        max_results (int): Максимальное количество результатов для поиска в Google Books API (необязательно).

    Returns:
        list: Список объектов данных о книгах.
    """
    # Проверяем наличие данных в базе данных
    books = Book.query.filter(Book.title.ilike(f'%{keyword}%')).all()

    if books:
        return books

    # Если данных нет в базе, делаем запрос к Google Books API
    return get_books_data_from_api(keyword, start_index, max_results)



def get_books_data_from_api(keyword, start_index=None, max_results=None):
    keyword = keyword.lower()
    if start_index is not None and max_results is not None:
        url = (
            f'https://www.googleapis.com/books/v1/volumes?q={keyword}&langRestrict=ru&startIndex={start_index}'
            f'&maxResults={max_results}&key={api_key}&projection=full')
        print(f"API Request URL: {url}")
    else:
        url = f'https://www.googleapis.com/books/v1/volumes?q={keyword}&langRestrict=ru&key={api_key}&projection=full'
        print(f"API Request URL: {url}")

    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get('items', [])

    return []


def update_book_details(google_id):
    """
    Функция для обновления данных о книге из базы данных или Google Books API.

    Args:
        google_id (str): Идентификатор книги в Google Books API.

    Returns:
        Book: Объект книги.
    """
    # Проверяем наличие данных о книге в базе данных
    book = Book.query.filter_by(google_id=google_id).first()

    if not book:
        # Если данных нет в базе, получаем данные из Google Books API
        book_data = get_book_data(google_id)

        if book_data:
            book = create_or_update_book(book_data)

    return book


@app.route('/books_by_category', methods=['GET'])
def books_by_category():
    categories = list(genres_data.keys())
    selected_category = request.args.get('category')
    selected_subcategory = request.args.get('subcategory')  # Добавляем получение выбранного поджанра
    print(f"Selected Category: {selected_category}")
    print(f"Selected Subcategory: {selected_subcategory}")  # Выводим выбранный поджанр для проверки
    print(f"Genres Data: {genres_data}")
    print(f"Selected Category from request.args: {selected_category}")
    page = request.args.get('page', default=1, type=int)
    books_per_page = 20
    start_index = (page - 1) * books_per_page

    # Если выбран жанр и поджанр и они есть в данных о жанрах, используем русское название поджанра
    if selected_category and selected_category in genres_data and selected_subcategory and \
            selected_subcategory in genres_data[selected_category]["subgenres"]:
        subcategory_name = genres_data[selected_category]["subgenres"][selected_subcategory]
        books_data = get_books_data_from_api(f'categories:{subcategory_name}', start_index, books_per_page)
    else:
        # Иначе используем английское название поджанра
        books_data = get_books_data_from_api(f'categories:{selected_subcategory}', start_index, books_per_page)

    random.shuffle(books_data)

    if books_data:
        books, total_pages = [create_or_update_book(book_data) for book_data in books_data], len(books_data)
    else:
        books, total_pages = [], 0

    print(f"Books Data: {books_data}")
    print(f"Books: {books}")

    return render_template('books_by_category.html', genres_data=genres_data, categories=categories,
                           selected_category=selected_category, selected_subcategory=selected_subcategory,
                           books=books, page=page, total_pages=total_pages)



@app.route('/books_by_author', methods=['GET'])
def books_by_author():
    author = request.args.get('author')
    page = request.args.get('page', default=1, type=int)
    books_per_page = 20
    start_index = (page - 1) * books_per_page

    books_data = get_books_data_from_api(author, start_index, books_per_page)

    if books_data:
        books = [create_or_update_book(book_data) for book_data in books_data]
        return render_template('books_by_author.html', author=author, books=books, genres_data=genres_data)

    return 'Error: Unable to retrieve books data.'


def add_genres_to_book(book, volume_info):
    categories_data = volume_info.get('categories', [])

    if isinstance(categories_data, list):
        # Очищаем текущие связи с жанрами
        book.genres = []

        for genre_name in set(categories_data):  # Используем set для уникальности и удаления повторов
            genre = Genre.query.filter_by(name=genre_name).first()

            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
                db.session.commit()

            book.genres.append(genre)

        # Присваиваем категории полю categories в виде строки
        book.category = ', '.join(categories_data)

        db.session.commit()

        print(f"Genres added to book: {list(set(categories_data))}")


@app.route('/best_sellers')
def best_sellers():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # По 5 книг в строке и 4 строки
    best_sellers = Book.query.filter_by(is_best_seller=True).paginate(page=page, per_page=per_page)

    return render_template('best_sellers.html', best_sellers=best_sellers,genres_data=genres_data)



@app.route('/search', methods=['GET', 'POST'])
def search():
    keyword = request.args.get('keyword')

    if not keyword:
        return render_template('search.html', keyword=keyword, books=[], genres_data=genres_data)

    try:
        books = search_books(keyword)
    except Exception as e:
        print(f"Error during book search: {e}")
        books = []

    return render_template('search.html', keyword=keyword, books=books, genres_data=genres_data)



def search_books(keyword):
    """
    Функция для поиска книг по ключевому слову.

    Args:
        keyword (str): Ключевое слово для поиска.

    Returns:
        list: Список объектов книг.
    """
    books_data = get_books_data_from_api(keyword)

    if books_data:
        books = [create_or_update_book(book_data) for book_data in books_data]
    else:
        books = []

    return books


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("POST request received")
        user = User.query.filter_by(username=request.form.get('username')).first()

        if user:
            print(f"User {user.username} found")  # Отладочное сообщение
            if user.check_password(request.form.get('password')):
                print("User authenticated")
                login_user(user)
                return redirect(url_for('profile'))
            else:
                print("Incorrect password")  # Отладочное сообщение
        else:
            print("User not found")  # Отладочное сообщение

    return render_template('login.html', genres_data=genres_data)




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password or not email:
            # Отобразите сообщение об ошибке
            return "Username,Password, email cannot be empty", 400
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', genres_data=genres_data)


@app.route('/my_books')
@login_required
def my_books():
    list_id = request.args.get('list_id', None)
    books = []
    if list_id:
        book_list = BookList.query.get(list_id)
        if book_list and book_list.user == current_user:
            books = book_list.books.all()
        else:
            return "Invalid list", 403
    else:
        for book_list in current_user.book_lists.all():
            books.extend((book_list.books.all()))
        books = list(set(books))

    all_lists = current_user.book_lists.all()

    # Обновим информацию о книгах, учитывая google_id
    for book in books:
        if book.google_id:
            # Запрос к Google Books API
            url = f'https://www.googleapis.com/books/v1/volumes/{book.google_id}?key={api_key}&projection=full'
            response = requests.get(url)
            if response.status_code == 200:
                book_data = response.json()
                book.google_id = book_data.get('id', None)
                db.session.commit()

    return render_template('my_books.html', books=books, all_lists=all_lists, selected_list=list_id,
                           genres_data=genres_data)


@app.route('/delete_book/<string:google_id>', methods=['POST'])
@login_required
def delete_book(google_id):
    book = Book.query.filter_by(google_id=google_id).first()

    if not book:
        return "Book not found", 404

    # Проверяем, принадлежит ли книга текущему пользователю
    if book.user_id != current_user.id:
        return "Permission denied", 403

    # Удаляем все комментарии к книге
    Comment.query.filter_by(book_id=book.id).delete()

    # Удаляем все рейтинги к книге
    Rating.query.filter_by(book_id=book.id).delete()

    db.session.delete(book)
    db.session.commit()

    return redirect(url_for('my_books'))


@app.route('/profile')
@login_required
def profile():
    all_lists = BookList.query.filter_by(user_id=current_user.id).all()

    return render_template('profile.html', all_lists=all_lists, genres_data=genres_data)


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Получение данных из формы
    name = request.form['name']
    email = request.form['email']
    username = request.form['username']
    about_me = request.form['about_me']
    
    # Получение файла из запроса
    avatar = request.files['avatar']

    # Сохранение файла на сервере
    if avatar:
        filename = secure_filename(avatar.filename)
        avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # UPLOAD_FOLDER - папка для сохранения файлов

    # Обновление данных пользователя в базе данных
    user = User.query.filter_by(id=current_user.id).first()
    user.name = name
    user.email = email
    user.username = username
    user.about_me = about_me
    user.avatar = filename  # Сохраняем имя файла в базе данных

    db.session.commit()  # Сохраняем изменения

    return redirect(url_for('profile'))


@app.route('/delete_list/<int:list_id>', methods=['POST'])
@login_required
def delete_list(list_id):
    list = BookList.query.get(list_id)
    if list:
        # Удалит все книги из списка
        for book in list.books:
            list.books.remove(book)
        db.session.delete(list)
        db.session.commit()
    return redirect(url_for('profile'))


@app.route('/edit_list/<int:list_id>', methods=['POST'])
@login_required
def edit_list(list_id):
    list = BookList.query.get(list_id)
    if list:
        new_name = request.form.get('new_name')
        list.name = new_name
        db.session.commit()
    return redirect(url_for('profile'))


@app.route('/update_list', methods=['POST'])
@login_required
def update_list():
    list_name = request.form.get('list_name')
    new_list = BookList(name=list_name, user=current_user)
    db.session.add(new_list)
    db.session.commit()
    return redirect(url_for('profile'))


@app.route('/add_to_list/<string:google_id>', methods=['POST'])
@login_required
def add_to_list(google_id):
    try:
        book = Book.query.filter_by(google_id=google_id).first()
        user_lists = current_user.book_lists.all()
        
        if not book:
            return "Book not found", 404

        # Проверяем, есть ли книга уже в списке пользователя
        for lst in user_lists:
            if book in lst.books:
                # Передаем сообщение в шаблон через переменную
                return render_template('select_list.html', book=book, lists=user_lists, genres_data=genres_data, message="Книга уже присутствует в вашем списке.")
        
        # Если книга не найдена в списках пользователя, переходим к выбору существующего списка
        return render_template('select_list.html', book=book, lists=user_lists, genres_data=genres_data)

    except Exception as e:
        return str(e)



@app.route('/remove_from_list/<string:google_id>', methods=['POST'])
@login_required
def remove_from_list(google_id):
    book = Book.query.filter_by(google_id=google_id).first()
    if not book:
        return "Book not found", 404

    for booklist in current_user.book_lists.all():
        if book in booklist.books:
            booklist.books.remove(book)

    db.session.commit()
    return redirect(url_for('my_books'))


@app.route('/submit_book_to_list', methods=['POST'])
@login_required
def submit_book_to_list():
    book_id = request.form.get('book_id')
    list_id = request.form.get('booklist')
    book = Book.query.get(book_id)
    book_list = BookList.query.get(list_id)

    if not book or not book_list:
        return "Book not found", 404

    if book not in book_list.books:
        book_list.books.append(book)
        db.session.commit()
    return redirect(url_for('my_books'))


@app.route('/create_list', methods=['GET', 'POST'])
@login_required
def create_list():
    if request.method == 'POST':
        list_name = request.form.get('list_name')
        new_list = BookList(name=list_name, user=current_user)
        db.session.add(new_list)
        db.session.commit()

        # Получаем информацию о книге из запроса
        book_id = request.form.get('book_id')
        book_identifier = request.form.get('book_identifier')

        # Проверяем, была ли нажата кнопка "Создать и добавить"
        if 'create_and_add' in request.form and book_id and book_identifier:
            # Получаем книгу по идентификатору (в вашем случае, google_id или isbn)
            book = Book.query.filter((Book.google_id == book_identifier) | (Book.isbn == book_identifier)).first()

            # Получаем созданный список
            created_list = BookList.query.filter_by(name=list_name, user=current_user).first()

            # Проверяем, что книга и список существуют
            if book and created_list:
                # Проверяем, что книга не находится уже в списке
                if book not in created_list.books:
                    created_list.books.append(book)
                    db.session.commit()

        # После завершения действий, перенаправляем пользователя
        return redirect(url_for('my_books'))

    return render_template('create_list.html')


@app.route('/add_comment/<string:google_id>', methods=['POST'])
@login_required
def add_comment(google_id):
    book = Book.query.filter_by(google_id=google_id).first()
    if not book:
        return "Book not found", 404

    content = request.form.get('content')
    comment = Comment(content=content, user_id=current_user.id, book_id=book.id)
    db.session.add(comment)
    db.session.commit()

    return redirect(url_for('book_details', google_id=google_id))


@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)

    if not comment:
        return "Comment not found", 404

    # Проверяем, принадлежит ли комментарий текущему пользователю
    if comment.user_id != current_user.id:
        return "Permission denied", 403

    db.session.delete(comment)
    db.session.commit()

    return redirect(url_for('book_details', google_id=comment.book.google_id))


@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get(comment_id)

    if not comment:
        return "Comment not found", 404

    # Проверяем, принадлежит ли комментарий текущему пользователю
    if comment.user_id != current_user.id:
        return "Permission denied", 403

    if request.method == 'POST':
        new_content = request.form.get('content')
        comment.content = new_content
        db.session.commit()

        return redirect(url_for('book_details', google_id=comment.book.google_id))

    return render_template('edit_comment.html', comment=comment)


@app.route('/rate/<string:google_id>', methods=['POST'])
@login_required
def rate_book(google_id):
    try:
        book = Book.query.filter_by(google_id=google_id).first()
        if not book:
            return jsonify({'error': 'Book not found'}), 404

        # Проверяем, голосовал ли пользователь ранее
        user_rating = Rating.query.filter_by(user_id=current_user.id, book_id=book.id).first()

        print(f"Received data: {request.form}")
        print(f"Received JSON data: {request.get_json()}")
        rating_value = int(request.json.get('rate'))

        if not user_rating:
            # Если у пользователя нет оценки, создаем новую запись
            new_rating = Rating(rate=rating_value, user_id=current_user.id, book_id=book.id)
            db.session.add(new_rating)
        else:
            # Если у пользователя уже есть оценка, обновляем ее
            user_rating.rate = rating_value

        db.session.commit()  # Сохраняем изменения в базе данных

        # Пересчитываем средний рейтинг
        average_rating, num_ratings = book.calculate_average_rating()

        # Возвращаем новый средний рейтинг и общее количество оценок
        return jsonify(
            {'average_rating': average_rating, 'num_ratings': num_ratings, 'current_user_rating': rating_value})

    except SQLAlchemyError as e:
        print(f'SQLAlchemy Error: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500
    except Exception as e:
        print(f'Unexpected Error: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/get_average_rating/<string:google_id>')
def get_average_rating(google_id):
    book = Book.query.filter_by(google_id=google_id).first()
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    # Вернем актуальный средний рейтинг из объекта книги
    average_rating = book.calculate_average_rating()

    return jsonify({'average_rating': average_rating})

def update_book_rating(book, volume_info):
    # Проверяем, есть ли ключ 'averageRating' в volume_info и он не равен None
    average_rating = volume_info.get('averageRating')
    rating = float(average_rating) if average_rating is not None else 0.0
    print(f"Рейтинг для {book.google_id}: {rating}")

    # Обновляем рейтинг только если есть данные о среднем рейтинге
    if average_rating is not None:
        book.rating = rating

    db.session.commit()
    print(f"Рейтинг обновлен для {book.google_id}: {book.rating}")

def recommend_books_for_user(user, num_recommendations=20):
    # Получаем все оценки пользователя
    user_ratings = Rating.query.filter_by(user_id=user.id).all()

    # Создаем словарь жанров и их суммарной оценки
    genre_ratings = {}

    for rating in user_ratings:
        # Используем запрос к базе данных для получения жанров каждой книги
        book_genres = Book.query.get(rating.book_id).genres
        for genre in book_genres:
            genre_name = genre.name
            if genre_name in genre_ratings:
                genre_ratings[genre_name] += rating.rate
            else:
                genre_ratings[genre_name] = rating.rate

    # Сортируем жанры по убыванию оценок
    sorted_genres = sorted(genre_ratings, key=genre_ratings.get, reverse=True)

    # Получаем подзапрос для выбора book_id книг, которые пользователь уже оценил
    subquery = Rating.query.filter_by(user_id=user.id).with_entities(Rating.book_id).subquery()

    # Получаем список книг для рекомендаций
    recommended_books = []
    for genre_name in sorted_genres:
        # Используем основной запрос, фильтруя книги, которые пользователь уже оценил
        books = Book.query.filter(
            ~Book.id.in_(subquery)
        ).filter_by(category=genre_name).limit(num_recommendations).all()

        recommended_books.extend(books)

        # Если мы достигли нужного количества рекомендаций, прекращаем цикл
        if len(recommended_books) >= num_recommendations:
            break

    return recommended_books

@app.route('/some_other_page')
def some_other_page():
    is_homepage = False
    return render_template('some_other_page.html')

@app.route('/recommendations')
@login_required
def user_recommendations():
    user = current_user
    recommended_books = recommend_books_for_user(user)

    return render_template('recommendations.html', user=user, recommended_books=recommended_books,
                           genres_data=genres_data)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
