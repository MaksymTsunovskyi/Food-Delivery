import pandas as pd
from faker import Faker
import random
import os
from sqlalchemy import create_engine, text

# Ініціалізація генератора
fake = Faker('uk_UA')
Faker.seed(42)
random.seed(42)

os.makedirs('data_lake', exist_ok=True)
print("Починаємо генерацію даних...")

# ==========================================
# 1. ТАБЛИЦІ ВИМІРІВ (DIMENSIONS)
# ==========================================
def generate_customers(n=500):
    data = []
    for i in range(1, n + 1):
        email = fake.email() if random.random() > 0.1 else None # 10% пропущених email для імітації брудних даних
        data.append({
            'customer_id': i,
            'full_name': fake.name(),
            'email': email,
            'city': fake.city(),
            'registration_date': fake.date_between(start_date='-2y', end_date='today')
        })
    df = pd.DataFrame(data)
    duplicates = df.sample(frac=0.05) # 5% дублікатів
    return pd.concat([df, duplicates], ignore_index=True)

def generate_restaurants(n=50):
    data = []
    categories = ['Суші', 'Піцца', 'Бургери', 'Українська', 'Азійська']
    for i in range(1, n + 1):
        data.append({
            'restaurant_id': i,
            'restaurant_name': fake.company(),
            'cuisine_type': random.choice(categories),
            'rating': round(random.uniform(3.5, 5.0), 1)
        })
    return pd.DataFrame(data)

def generate_couriers(n=40):
    data = []
    vehicles = ['Велосипед', 'Скутер', 'Пішки', 'Автомобіль']
    for i in range(1, n + 1):
        data.append({
            'courier_id': i,
            'courier_name': fake.name(),
            'vehicle_type': random.choice(vehicles),
            'phone': fake.phone_number()
        })
    return pd.DataFrame(data)

# ==========================================
# 2. ТАБЛИЦІ ФАКТІВ (FACTS)
# ==========================================
def generate_orders(n, customer_ids, restaurant_ids, courier_ids):
    data = []
    for i in range(1, n + 1):
        data.append({
            'order_id': fake.uuid4(),
            'customer_id': random.choice(customer_ids),
            'restaurant_id': random.choice(restaurant_ids),
            'courier_id': random.choice(courier_ids),
            'order_amount': round(random.uniform(150.0, 1200.0), 2),
            'order_date': fake.date_time_between(start_date='-1y', end_date='now')
        })
    return pd.DataFrame(data)

def generate_routes(orders_df):
    data = []
    statuses = ['delivered', 'cancelled', 'delayed']
    for _, row in orders_df.iterrows():
        data.append({
            'route_id': fake.uuid4(),
            'order_id': row['order_id'],
            'delivery_time_mins': random.randint(15, 90),
            'status': random.choices(statuses, weights=[85, 10, 5])[0]
        })
    return pd.DataFrame(data)

# Генерація DataFrames
df_customers = generate_customers()
df_restaurants = generate_restaurants()
df_couriers = generate_couriers()

unique_cust_ids = df_customers['customer_id'].dropna().unique().tolist()
rest_ids = df_restaurants['restaurant_id'].tolist()
courier_ids = df_couriers['courier_id'].tolist()

df_orders = generate_orders(5000, unique_cust_ids, rest_ids, courier_ids)
df_routes = generate_routes(df_orders)

# Збереження у форматі Parquet
df_customers.to_parquet('data_lake/raw_customers.parquet', index=False)
df_restaurants.to_parquet('data_lake/raw_restaurants.parquet', index=False)
df_couriers.to_parquet('data_lake/raw_couriers.parquet', index=False)
df_orders.to_parquet('data_lake/raw_orders.parquet', index=False)
df_routes.to_parquet('data_lake/raw_routes.parquet', index=False)

print("Генерація файлів Parquet успішно завершена. Завантаження у PostgreSQL...")

# ==========================================
# 3. ЗАВАНТАЖЕННЯ (LOAD) У DWH
# ==========================================
DB_URL = "postgresql+psycopg2://admin:adminpassword@localhost:5432/food_delivery_dwh"
engine = create_engine(DB_URL)

def load_data_to_dwh():
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()
        
        # if_exists='replace' імітує повне перезавантаження
        df_customers.to_sql('customers', engine, schema='raw', if_exists='replace', index=False)
        df_restaurants.to_sql('restaurants', engine, schema='raw', if_exists='replace', index=False)
        df_couriers.to_sql('couriers', engine, schema='raw', if_exists='replace', index=False)
        df_orders.to_sql('food_orders', engine, schema='raw', if_exists='replace', index=False)
        df_routes.to_sql('delivery_routes', engine, schema='raw', if_exists='replace', index=False)
        
    print("Дані успішно завантажені у схему 'raw'!")

if __name__ == "__main__":
    load_data_to_dwh()