from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG("pakakumi_scraper",
         start_date=datetime(2026,1,2),
         schedule_interval="@hourly",
         catchup=False) as dag:

    run_scraper = BashOperator(
        task_id="run_scraper",
        bash_command="docker-compose -f ../docker-compose.yml run scraper"
    )
