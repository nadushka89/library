# import random
# import string
#
# def generate_random_username():
#     # Генерация случайного имени пользователя
#     prefix = ''.join(random.choices(string.ascii_letters, k=5))
#     suffix = random.randint(100, 999)
#     return f'{prefix}_{suffix}'
#
# def generate_random_password():
#     # Генерация случайного пароля
#     characters = string.ascii_letters + string.digits
#     password = ''.join(random.choices(characters, k=8))
#     return password
#
# def generate_random_email():
#     # Генерация случайного email
#     domains = ['inbox.ru', 'mail.ru', 'yandex.com', 'gmail.com']
#     username = generate_random_username()
#     domain = random.choice(domains)
#     return f'{username}@{domain}'
#
# # Создание списка пользователей
# users = []
# for _ in range(20):
#     username = generate_random_username()
#     password = generate_random_password()
#     email = generate_random_email()
#     users.append((username, password, email))
#
# # Вывод данных пользователей
# for user in users:
#     print(user)