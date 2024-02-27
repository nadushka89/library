
# @app.route('/')
# def index():
#     categories = {"history", "fiction", "mystery", "fantasy", "biography", "science", "romance",
#                   "adventure", "horror", "classics", "biotechnology", "social", "public", "health", "medical",
#                   "general"}
#
#     url = f'https://www.googleapis.com/books/v1/volumes?q={categories}&langRestrict=eng&maxResults=11&key={api_key}&projection=full'
#     response = requests.get(url)
#     # информация о статусе запроса и данные API
#     # print(f"API Response Status Code: {response.status_code}")
#     # print(f"API Response Data: {response.json()}")
#
#     if response.status_code == 200:
#         books_data = response.json().get('items', [])
#
#         all_books = []
#
#         if books_data:
#             for book_data in books_data:
#                 google_id = book_data.get('id') or book_data.get('id', None)
#
#                 print(f"Book Title: {book_data.get('volumeInfo', {}).get('title', 'No Title')}")
#                 if not any(book.google_id == google_id for book in all_books):
#                     title = book_data['volumeInfo']['title']
#                     author = ", ".join(book_data['volumeInfo'].get('authors', ['Unknown Author']))
#                     description = book_data['volumeInfo'].get('description', '')
#                     volume_info = book_data['volumeInfo']
#                     published_date = volume_info.get('publishedDate', None)
#                     if published_date:
#                         published_date = parser.parse(published_date).date()
#                     else:
#                         published_date = None
#                     image_links = volume_info.get('imageLinks', {})
#                     cover_image = image_links.get('smallThumbnail') or image_links.get('thumbnail', None)
#                     rating = book_data['volumeInfo'].get('averageRating', 0)
#
#                     # Проверяем, является ли книга бестселлером
#                     is_best_seller = any(
#                         category.lower() in categories for category in book_data['volumeInfo'].get('categories', []))
#
#                     book = Book.query.filter(Book.google_id == google_id).first()
#                     if not book:
#                         book = Book(google_id=google_id, title=title, author=author, description=description,
#                                     cover_image=cover_image, published_date=published_date, is_best_seller=is_best_seller)
#                         book.rating = rating
#                         db.session.add(book)
#                         db.session.commit()
#                     else:
#                         book.cover_image = cover_image
#                         if rating is not None:
#                             book.rating = rating
#                         book.is_best_seller = is_best_seller
#                         db.session.commit()
#
#                     all_books.append(book)
#
#             # Фильтруем только бестселлеры
#         bestsellers = Book.query.filter_by(is_best_seller=True).all()
#         random.shuffle(bestsellers)
#         return render_template('index.html', bestsellers=bestsellers)
#
#     else:
#         all_books = []  # Инициализация пустым списком в случае ошибки
#
#     print("All Books:", all_books)
#     return render_template('index.html', all_books=all_books)


#
# @app.route('/books')
# def books():
#     keywords = ["history", "fiction", "mystery", "fantasy", "biography", "science", "romance",
#                 "adventure", "horror", "classics"]
#     random_keyword = random.choice(keywords)
#     # Отправляем GET-запрос к Google Books API с использованием API-ключа
#     url = (f'https://www.googleapis.com/books/v1/volumes?q={random_keyword}&langRestrict=ru&maxResults=20&key={api_key}'
#            f'&projection=full')
#     response = requests.get(url)
#     print(response.text)
#
#     if response.status_code == 200:
#         books_data = response.json().get('items', [])
#
#         books = []
#
#         for book_data in books_data:
#             google_id = book_data.get('id', None)
#             isbn = None
#             title = book_data['volumeInfo']['title']
#             author = ", ".join(book_data['volumeInfo'].get('authors', ['Неизвестный автор (Unknown Author)']))
#             description = book_data['volumeInfo'].get('description', '')
#             volume_info = book_data['volumeInfo']
#             published_date = volume_info.get('publishedDate', None)
#             if published_date:
#                 published_date = parser.parse(published_date).date()
#             else:
#                 published_date = None
#             image_links = volume_info.get('imageLinks', {})
#             cover_image = image_links.get('smallThumbnail') or image_links.get('thumbnail', None)
#
#             # рейтинг книги из Google Books API
#             rating = book_data['volumeInfo'].get('averageRating', 0)
#             is_best_seller = any(
#                 keyword.lower() in keywords for keyword in book_data['volumeInfo'].get('categories', []))
#             book = Book.query.filter_by(google_id=google_id).first()
#             if not book:
#                 book = Book(google_id=google_id, title=title, author=author, description=description,
#                             cover_image=cover_image, published_date=published_date, is_best_seller=is_best_seller)
#                 book.rating = rating
#                 db.session.add(book)
#                 db.session.commit()
#             else:
#                 book.cover_image = cover_image
#                 if rating is not None:
#                     book.rating = rating
#                 db.session.commit()
#
#             books.append(book)
#
#         return render_template('books.html', books=books)
#
#     else:
#         return 'Error: Unable to retrieve books data.'
#
# @app.route('/book/<string:google_id>')
# def book_details(google_id):
#     # Пытаемся найти книгу в базе данных
#     book = Book.query.filter_by(google_id=google_id).first()
#     book_data = None
#     published_date = None  # Объявляем published_date здесь
#     page_count = None  # Объявляем page_count здесь
#
#     if not book:
#         # Если книги нет в базе, делаем запрос к Google Books API
#         url = f'https://www.googleapis.com/books/v1/volumes/{google_id}?key={api_key}&projection=full'
#         response = requests.get(url)
#
#         if response.status_code == 200:
#             book_data = response.json()['volumeInfo']
#             print("Received book data:", book_data)
#
#             # Пытаемся найти книгу в базе данных
#             book = Book.query.filter_by(google_id=google_id).first()
#
#             # Создаем новую запись в базе данных или обновляем существующую
#             if not book:
#                 try:
#                     published_date_str = book_data.get('publishedDate', None)
#                     published_date = parser.parse(published_date_str).date() if published_date_str else None
#                 except ValueError:
#                     published_date = None
#                 page_count = book_data.get('pageCount', None)
#
#                 book = Book(
#                     google_id=google_id,
#                     title=book_data.get('title', 'Unknown Title'),
#                     author=", ".join(book_data.get('authors', ['Unknown Author'])),
#                     description=book_data.get('description', ''),
#                     pages=page_count,
#                     category=", ".join(book_data.get('categories', [])),
#                     cover_image=book_data['imageLinks'].get('mediumThumbnail') or
#                                 book_data['imageLinks'].get('smallThumbnail') or
#                                 book_data['imageLinks'].get('thumbnail', None),
#                     published_date=published_date,
#                     rating=book_data.get('averageRating', 0),
#                 )
#
#                 db.session.add(book)
#                 db.session.commit()
#             else:
#                 # Обновление существующей записи
#                 try:
#                     published_date_str = book_data.get('publishedDate', None)
#                     published_date = parser.parse(published_date_str).date() if published_date_str else None
#                 except ValueError:
#                     published_date = None
#
#                 page_count = book_data.get('pageCount', None)
#
#                 book.title = book_data.get('title', 'Unknown Title')
#                 book.author = ", ".join(book_data.get('authors', ['Unknown Author']))
#                 book.description = book_data.get('description', '')
#                 book.pages = page_count
#                 book.category = ", ".join(book_data.get('categories', []))
#                 book.cover_image = book_data['imageLinks'].get('mediumThumbnail') or \
#                                    book_data['imageLinks'].get('smallThumbnail') or \
#                                    book_data['imageLinks'].get('thumbnail', None)
#                 book.published_date = published_date
#                 book.rating = book_data.get('averageRating', 0)
#                 db.session.commit()
#
#         else:
#             return "Error: Unable to retrieve book data"
#
#     comments = Comment.query.filter_by(book_id=book.id).order_by(Comment.timestamp.desc()).all()
#     rating = Rating.query.filter_by(book_id=book.id).all()
#     cover_image = book.cover_image
#
#     current_user_rating = None
#     is_in_list = False
#
#     if current_user.is_authenticated:
#         user_rating = Rating.query.filter_by(book_id=book.id, user_id=current_user.id).first()
#         if user_rating:
#             current_user_rating = user_rating.rate
#
#         user_lists = current_user.book_lists.all()
#         for user_list in user_lists:
#             if book in user_list.books:
#                 is_in_list = True
#                 break
#
#     return render_template('books_details.html', book=book, google_id=google_id,
#                            book_data=book_data, comments=comments, cover_image=cover_image, rating=rating,
#                            current_user_rating=current_user_rating, is_in_list=is_in_list, published_date=published_date)
#
# @app.route('/books_by_category', methods=['GET'])
# def books_by_category():
#     selected_category = request.args.get('category')
#     page = request.args.get('page', default=1, type=int)
#     books_per_page = 20
#
#     if selected_category:
#         books_data, total_pages = get_books_data(selected_category, page, books_per_page)
#         books = process_books_data(books_data)
#
#         return render_template('books_by_category.html', category=selected_category, books=books,
#                                page=page, total_pages=total_pages)
#
#     else:
#         # Если пользователь не выбрал категорию, отобразим все книги
#         books_data, total_pages = get_books_data(None, page, books_per_page)
#         books = process_books_data(books_data)
#
#         return render_template('books_by_category.html', category='All Books', books=books, page=page, total_pages=total_pages)


#
# def get_books_data(selected_category, page, books_per_page):
#     start_index = (page - 1) * books_per_page
#     url = f'https://www.googleapis.com/books/v1/volumes?q=subject:{selected_category}&langRestrict=ru&langRestrict=en&maxResults={books_per_page}&startIndex={start_index}&key={api_key}&projection=full'
#     response = requests.get(url)
#
#     if response.status_code == 200:
#         books_data = response.json().get('items', [])
#         total_results = int(response.json().get('totalItems', 0))
#         total_pages = (total_results + books_per_page - 1) // books_per_page
#
#         return books_data, total_pages
#
#     return [], 0

# def process_books_data(books_data):
#     books = []
#
#     for book_data in books_data:
#         google_id = book_data.get('id')
#         title = book_data['volumeInfo']['title']
#         author = ", ".join(book_data['volumeInfo'].get('authors', ['Неизвестный автор (Unknown Author)']))
#         description = book_data['volumeInfo'].get('description', '')
#         volume_info = book_data['volumeInfo']
#         image_links = volume_info.get('imageLinks', {})
#         cover_image = image_links.get('smallThumbnail') or image_links.get('thumbnail', None)
#         rating = book_data['volumeInfo'].get('averageRating', 0)
#
#         book = Book.query.filter_by(google_id=google_id).first()
#
#         if not book:
#             book = Book(google_id=google_id, title=title, author=author,
#                         description=description, rating=rating, cover_image=cover_image)
#             add_genres_to_book(book, volume_info)
#
#             # Добавляем обработку published_date
#             try:
#                 published_date_str = volume_info.get('publishedDate', None)
#                 published_date = parser.parse(published_date_str).date() if published_date_str else None
#                 book.published_date = published_date
#             except ValueError:
#                 book.published_date = None
#
#             db.session.add(book)
#         else:
#             book.title = title
#             book.author = author
#             book.description = description
#             book.cover_image = cover_image
#             book.rating = rating
#             add_genres_to_book(book, volume_info)
#
#             # Добавляем обработку published_date
#             try:
#                 published_date_str = volume_info.get('publishedDate', None)
#                 published_date = parser.parse(published_date_str).date() if published_date_str else None
#                 book.published_date = published_date
#             except ValueError:
#                 book.published_date = None
#
#         db.session.commit()
#         books.append(book)
#
#     return books


#
# @app.route('/best_sellers')
# def best_sellers():
#     page = request.args.get('page', 1, type=int)
#     per_page = 20  # По 5 книг в строке и 4 строки
#     best_sellers = Book.query.filter_by(is_best_seller=True).paginate(page=page, per_page=per_page)
#
#     return render_template('best_sellers.html', best_sellers=best_sellers)

# def search_books(keyword):
#     service = build('books', 'v1', developerKey=api_key)
#     response = service.volumes().list(q=keyword, maxResults=20).execute()
#     books_data = response.get('items', [])
#
#     books = []
#     for book_data in books_data:
#         google_id = book_data.get('id', None)
#         title = book_data['volumeInfo'].get('title', 'Unknown Title')
#         author = ", ".join(book_data['volumeInfo'].get('authors', ['Unknown Author']))
#         description = book_data['volumeInfo'].get('description', '')
#         volume_info = book_data['volumeInfo']
#         image_links = volume_info.get('imageLinks', {})
#         cover_image = image_links.get('mediumThumbnail') or image_links.get('smallThumbnail') or image_links.get(
#             'thumbnail', None)
#
#         book = Book(
#             google_id=google_id,
#             title=title,
#             author=author,
#             description=description,
#             cover_image=cover_image
#         )
#         books.append(book)
#
#     return books

# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     keyword = request.args.get('keyword') if request.method == 'GET' else request.form.get('keyword')
#
#     if not keyword:
#         return render_template('search.html', keyword=keyword, books=[])
#
#     try:
#         books = search_books(keyword)
#     except Exception as e:
#         print(f"Error during book search: {e}")
#         books = []
#
#     return render_template('search.html', keyword=keyword, books=books)

