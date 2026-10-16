🍔 Food Delivery Data Warehouse (Modern Data Stack)

📌 Про проєкт

Цей репозиторій містить реалізацію першого етапу побудови аналітичного сховища даних (Data Warehouse) для сервісу доставки їжі. Проєкт виконується за сучасною парадигмою ELT (Extract, Load, Transform).

На даному етапі (Лабораторна робота №1) реалізовано зону посадки даних (Raw Layer) та Data Lake. Транзакційна система (OLTP) імітується за допомогою Python, після чого дані "як є" (as is) завантажуються в аналітичну базу даних.

🏗 Архітектура

Data Generator (Python): Імітує роботу бекенду додатку доставки їжі. Генерує 5 сутностей: customers, restaurants, couriers, food_orders, delivery_routes.

Data Lake (Parquet): Зберігає плоску резервну копію "сирих" даних.

Data Warehouse (PostgreSQL / Docker): Ізольована аналітична база даних (OLAP), куди дані завантажуються для подальшої трансформації.

🛠 Технологічний стек

Python 3.9+ (Pandas, Faker, SQLAlchemy)

Docker & Docker Compose

PostgreSQL 15

Parquet

🚀 Інструкція із запуску (Як розгорнути локально)

1. Клонування репозиторію

git clone <ваше_посилання_на_репозиторій>
cd Food-Delivery


2. Налаштування середовища (Python)

Створіть та активуйте віртуальне середовище:

Для Windows (PowerShell):

python -m venv venv
venv\Scripts\Activate.ps1


Для Linux/Mac:

python3 -m venv venv
source venv/bin/activate


Встановіть необхідні залежності:

pip install -r requirements.txt


3. Запуск інфраструктури (Docker)

Переконайтеся, що Docker Desktop запущений, та підніміть контейнер з базою даних PostgreSQL у фоновому режимі:

docker-compose up -d


4. Генерація та завантаження даних (Extract & Load)

Запустіть скрипт для створення даних та їх завантаження в схему raw бази даних:

python data_generator.py


Якщо все пройшло успішно, ви побачите повідомлення Дані успішно завантажені у схему 'raw'!, а в корені проєкту з'явиться папка data_lake/.

📁 Структура проєкту

data_generator.py — головний скрипт генерації та інгістування (завантаження) даних.

docker-compose.yml — конфігурація для розгортання DWH (PostgreSQL).

requirements.txt — список залежностей Python.

data_lake/ — директорія для зберігання flat-файлів у форматі Parquet.