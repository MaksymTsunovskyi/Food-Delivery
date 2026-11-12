# Food Delivery Data Warehouse

## Опис проєкту
Репозиторій містить реалізацію аналітичного сховища даних (Data Warehouse) для сервісу доставки їжі. Проєкт побудовано за сучасною парадигмою ELT (Extract, Load, Transform) і логічно поділено на два етапи:
1. **Extract & Load (Зона посадки та Data Lake):** Імітація роботи транзакційної системи (OLTP), генерація сирих даних та їх завантаження в аналітичну базу даних.
2. **Transform (Трансформація даних):** Очищення даних, видалення дублікатів та побудова фінальних аналітичних вітрин (Data Marts) за допомогою dbt.

## Архітектура системи
* **Data Generator (Python):** Імітує роботу бекенду додатку. Синтезує 5 сутностей (`customers`, `restaurants`, `couriers`, `food_orders`, `delivery_routes`).
* **Data Lake (Parquet):** Зберігає плоску резервну копію "сирих" даних.
* **Data Warehouse (PostgreSQL / Docker):** Ізольована аналітична база даних (OLAP).
* **dbt (data build tool):** Відповідає за шар трансформації, матеріалізуючи SQL-моделі рівнів Staging та Mart.

## Технологічний стек
* **Мова:** Python 3.11 (Pandas, Faker, SQLAlchemy)
* **Інфраструктура:** Docker, Docker Compose
* **СУБД:** PostgreSQL 15
* **Оркестрація трансформацій:** dbt (dbt-core, dbt-postgres)
* **Формати даних:** Parquet

## Локальне розгортання

### 1. Підготовка середовища
Клонуйте репозиторій та перейдіть у директорію проєкту:
```bash
git clone <ваше_посилання_на_репозиторій>
cd Food-Delivery

Створіть та активуйте віртуальне середовище (рекомендовано Python 3.11 для повної сумісності з dbt):
# Для Windows (PowerShell)
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

Встановіть необхідні залежності:
pip install -r requirements.txt

2. Запуск інфраструктури (Docker)
Переконайтеся, що Docker Desktop запущений, та підніміть контейнер з базою даних PostgreSQL у фоновому режимі:
docker-compose up -d

3. Етап Extract & Load (Лабораторна робота №1)
Запустіть скрипт для генерації даних. Дані будуть завантажені у схему raw, а в корені проєкту з'явиться папка data_lake/ з бекапами:

python data_generator.py

4. Етап Transform (Лабораторна робота №2)
Перейдіть до директорії dbt-проєкту та запустіть конвеєр трансформації. Інструмент автоматично створить схему analytics і розгорне в ній очищені таблиці та вітрини:
cd food_delivery_transform
dbt debug
dbt run

Структура репозиторію
data_generator.py — головний скрипт генерації та інгістування даних.

docker-compose.yml — конфігурація для розгортання DWH.

requirements.txt — список залежностей Python.

data_lake/ — директорія для зберігання flat-файлів (Parquet).

food_delivery_transform/ — директорія dbt-проєкту із SQL-моделями (шари stg та mart).