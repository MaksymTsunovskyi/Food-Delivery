from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os
import sys

# Додаємо шлях до скриптів
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))
from data_generator import load_data_to_dwh

# Абсолютні шляхи для Linux/WSL
DBT_PROJECT_DIR = '/mnt/c/Users/sa3/Documents/GitHub/Food-Delivery/food_delivery_transform'

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0, # Вимикаємо повторні спроби, щоб таск падав одразу і не змушував чекати
}

with DAG(
    'food_delivery_elt_pipeline',
    default_args=default_args,
    description='Автоматизований ELT конвеєр доставки їжі (ЛР3)',
    schedule_interval='@daily',
    catchup=False
) as dag:

    extract_load_task = PythonOperator(
        task_id='extract_and_load_raw_data',
        python_callable=load_data_to_dwh
    )

   # Task 2: Трансформація даних через dbt
    dbt_run_task = BashOperator(
        task_id='dbt_run_transformations',
        bash_command=f'dbt run --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROJECT_DIR} --no-send-anonymous-usage-stats'
    )

    # Task 3: Перевірка якості даних через dbt test
    dbt_test_task = BashOperator(
        task_id='dbt_test_transformations',
        bash_command=f'dbt test --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROJECT_DIR} --no-send-anonymous-usage-stats'
    )

    extract_load_task >> dbt_run_task >> dbt_test_task