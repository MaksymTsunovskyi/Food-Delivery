import io
import os
import random
from faker import Faker
import pandas as pd
import psycopg2

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
        email = fake.email() if random.random() > 0.1 else None # 10% NULL
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
# 3. ПРЯМЕ ЗАВАНТАЖЕННЯ (COPY) У DWH БЕЗ PANDAS TO_SQL
# ==========================================
def save_df_to_postgres(df, table_name, cur):
    cur.execute(f"DROP TABLE IF EXISTS raw.{table_name} CASCADE;")
    
    type_map = {
        'int64': 'BIGINT',
        'float64': 'DOUBLE PRECISION',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'TIMESTAMP'
    }
    
    cols = []
    for col_name, dtype in df.dtypes.items():
        pg_type = type_map.get(str(dtype), 'TEXT')
        cols.append(f'"{col_name}" {pg_type}')
        
    create_sql = f"CREATE TABLE raw.{table_name} (\n    " + ",\n    ".join(cols) + "\n);"
    cur.execute(create_sql)
    
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=True)
    buffer.seek(0)
    
    cur.copy_expert(f"COPY raw.{table_name} FROM STDIN WITH CSV HEADER NULL ''", buffer)

def load_data_to_dwh():
    conn = psycopg2.connect(
        dbname="food_delivery_dwh",
        user="admin",
        password="adminpassword",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()
    
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    
    tables = {
        'customers': df_customers,
        'food_orders': df_orders,
        'restaurants': df_restaurants,
        'couriers': df_couriers,
        'delivery_routes': df_routes
    }
    
    for table_name, df in tables.items():
        print(f"Завантаження {table_name}...")
        save_df_to_postgres(df, table_name, cur)
        
    conn.commit()
    cur.close()
    conn.close()
    print("Дані успішно завантажені у схему 'raw'!")

if __name__ == "__main__":
    load_data_to_dwh()