import os
import random
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, text

# Рядок підключення до PostgreSQL DWH
DB_URL = "postgresql://admin:adminpassword@localhost:5432/food_delivery_dwh"


def generate_customers(fake: Faker, num: int = 500) -> pd.DataFrame:
    """Генерація виміру клієнтів із навмисними пропусками та дублікатами для dbt."""
    data = []
    for i in range(1, num + 1):
        # 10% пропущених email для перевірки очищення в staging-шарі
        email = fake.email() if random.random() > 0.1 else None
        data.append({
            "customer_id": i,
            "name": fake.name(),
            "email": email,
            "phone": fake.phone_number(),
            "city": fake.city(),
            "registration_date": fake.date_between(start_date="-2y", end_date="today"),
        })

    df = pd.DataFrame(data)
    # Додаємо 5% дублікатів для перевірки дедуплікації (ROW_NUMBER) у dbt
    duplicates = df.sample(frac=0.05, random_state=42)
    return pd.concat([df, duplicates], ignore_index=True)


def generate_restaurants(fake: Faker, num: int = 40) -> pd.DataFrame:
    """Генерація виміру ресторанів."""
    cuisines = ["Італійська", "Японська", "Українська", "Бургери", "Грузинська", "Азійська"]
    prefixes = ["Смачна", "Велика", "Стара", "Панська", "Міська", "Сонячна"]
    nouns = ["Кухня", "Піцерія", "Хата", "Тераса", "Пекарня", "Ресторація"]

    data = []
    for i in range(1, num + 1):
        data.append({
            "restaurant_id": i,
            "name": f"{random.choice(prefixes)} {random.choice(nouns)} #{i}",
            "cuisine_type": random.choice(cuisines),
            "city": fake.city(),
            "rating": round(random.uniform(3.6, 5.0), 1),
        })
    return pd.DataFrame(data)


def generate_couriers(fake: Faker, num: int = 60) -> pd.DataFrame:
    """Генерація виміру кур'єрів."""
    vehicles = ["Велосипед", "Скутер", "Авто", "Піший"]
    data = []
    for i in range(1, num + 1):
        data.append({
            "courier_id": i,
            "name": fake.name(),
            "vehicle_type": random.choice(vehicles),
            "rating": round(random.uniform(4.0, 5.0), 1),
        })
    return pd.DataFrame(data)


def generate_food_orders(
    fake: Faker,
    customer_ids: list[int],
    restaurant_ids: list[int],
    courier_ids: list[int],
    num: int = 5000,
) -> pd.DataFrame:
    """Генерація факту замовлень із реалістичним розподілом активності клієнтів."""
    # Розподіл Ципфа: перші клієнти у списку замовляють значно частіше за інших
    customer_weights = [1.0 / ((idx + 1) ** 0.85) for idx in range(len(customer_ids))]

    data = []
    for i in range(1, num + 1):
        data.append({
            "order_id": i,
            "customer_id": random.choices(customer_ids, weights=customer_weights, k=1)[0],
            "restaurant_id": random.choice(restaurant_ids),
            "courier_id": random.choice(courier_ids),
            "order_amount": round(random.uniform(150.0, 1800.0), 2),
            "order_date": fake.date_time_between(start_date="-1y", end_date="now"),
            "status": random.choices(
                ["delivered", "cancelled", "delayed"],
                weights=[82, 10, 8],
                k=1,
            )[0],
        })
    return pd.DataFrame(data)


def generate_delivery_routes(df_orders: pd.DataFrame) -> pd.DataFrame:
    """Генерація факту маршрутів доставки, прив'язаних до кожного замовлення."""
    data = []
    for idx, row in df_orders.iterrows():
        is_cancelled = row["status"] == "cancelled"
        data.append({
            "route_id": idx + 1,
            "order_id": int(row["order_id"]),
            "courier_id": int(row["courier_id"]),
            "distance_km": round(random.uniform(1.0, 14.5), 2),
            "delivery_time_mins": 0 if is_cancelled else random.randint(15, 75),
            "route_status": "aborted" if is_cancelled else "completed",
        })
    return pd.DataFrame(data)


def load_data_to_dwh() -> None:
    """Генерує дані за варіантом 21 та завантажує їх у схему raw PostgreSQL."""
    fake = Faker("uk_UA")
    Faker.seed(42)
    random.seed(42)

    print("Генерація вимірів (customers, restaurants, couriers)...")
    df_customers = generate_customers(fake, num=500)
    df_restaurants = generate_restaurants(fake, num=40)
    df_couriers = generate_couriers(fake, num=60)

    # Перемішуємо унікальні ID клієнтів перед призначенням ваг, щоб лідери не мали ID 1..5
    unique_customer_ids = df_customers["customer_id"].dropna().unique().tolist()
    random.shuffle(unique_customer_ids)

    restaurant_ids = df_restaurants["restaurant_id"].tolist()
    courier_ids = df_couriers["courier_id"].tolist()

    print("Генерація фактів (food_orders, delivery_routes)...")
    df_orders = generate_food_orders(
        fake, unique_customer_ids, restaurant_ids, courier_ids, num=5000
    )
    df_routes = generate_delivery_routes(df_orders)

    # Збереження копії у форматі Parquet (шар Data Lake)
    os.makedirs("data_lake", exist_ok=True)
    df_customers.to_parquet("data_lake/raw_customers.parquet", index=False)
    df_restaurants.to_parquet("data_lake/raw_restaurants.parquet", index=False)
    df_couriers.to_parquet("data_lake/raw_couriers.parquet", index=False)
    df_orders.to_parquet("data_lake/raw_food_orders.parquet", index=False)
    df_routes.to_parquet("data_lake/raw_delivery_routes.parquet", index=False)

    # Завантаження у PostgreSQL (схема raw, Full Load через replace)
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()

    tables = {
        "customers": df_customers,
        "restaurants": df_restaurants,
        "couriers": df_couriers,
        "food_orders": df_orders,
        "delivery_routes": df_routes,
    }

    for table_name, df in tables.items():
        print(f"Завантаження raw.{table_name} ({len(df)} рядків)...")
        df.to_sql(table_name, engine, schema="raw", if_exists="replace", index=False)

    print("Усі дані успішно оновлено у схемі 'raw'!")


if __name__ == "__main__":
    load_data_to_dwh()