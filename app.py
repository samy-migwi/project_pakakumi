
import os 
import time 
import psycopg2 
from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.chrome.options import Options 
import logging
import traceback
from dotenv import load_dotenv


# Headless Chrome inside Docker 
def get_driver(): 
    chrome_options = Options() 
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--disable-gpu") 
    chrome_options.add_argument("--window-size=1920,1080") 
    return webdriver.Chrome(options=chrome_options)

driver=get_driver()
url = "https://play.pakakumi.com/"
driver.get(url)
wait = WebDriverWait(driver, 10)

# for production i will swtich from printing on console to logging
#logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()

#database config
"""DB_CONFIG={
    "host":os.getenv('DB_HOST'),
    
    'database':os.getenv('DB_NAME'),
    'user':os.getenv('DB_USER'),
    'password':os.getenv('DB_PASSWORD'),
    'port':os.getenv('DB_PORT')
}"""
# we have now configed our db let now define a function to connect to the db
def get_db_connection():
    try:
        conn= psycopg2.connect(
            
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            #sslmode="require"
            )
        logging.info('Database connection established')
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection error",exc_info=True)
        tb=traceback.format_exc()
        logging.debug(f"Traceback details:\n{tb}")
        raise
# we have connected to our db let define how to  insert data
def insert_data(bust_number,hash_code,timestamp):
    if bust_number=="Login":
        logging.warning("Skipping insert: bust number is 'Login' ")
        return False

           
    bust_number = float(bust_number[:-1])
    
    conn=get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(""" 
                            INSERT INTO bust_data(bust_number,hash_code,timestamp)
                            VALUES (%s,%s,%s)
                            ON CONFLICT (bust_number,hash_code) DO NOTHING
                            """, (bust_number,hash_code,timestamp))
                conn.commit()
                logging.info(f"Inserted bust={bust_number},hash={hash_code},time={timestamp}")
        except psycopg2.Error as e:
            logging.error(f"Error inserting data",exc_info=True)
            raise
        finally:
            conn.close()
#our connection is ready for data lets now  make a "pipeline" to get the data
def scrape_data():
    previous_entry= None

    while True:
        try:
            bust_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.css-19toqs6")))
            hash_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.css-10zyika")))

            bust_number = bust_element.text
            #let remove x  in the bust number 
            #bust_number = float(bust_text[:-1])
            hash_code = hash_element.get_attribute("value")
            current_entry=(bust_number,hash_code)

            if current_entry != previous_entry:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                
                
                logging.info('New data captured')
                

                insert_data(bust_number, hash_code, timestamp)
                
                previous_entry = current_entry

            time.sleep(1)

        except Exception as e:
            logging.error(f" Scraping error",exc_info=True)
            tb=traceback.format_exc()
            logging.debug(f"Scraping traceback details:\n{tb}")
            time.sleep(5)
            try:
                logging.warning("Attempting to reconnect...")
                driver.get(url)
                wait = WebDriverWait(driver, 10)
            except Exception as reconnect_error:
                logging.error(f"Reconnection failed",exc_info=True)
                tb_reconnect = traceback.format_exc() 
                logging.debug(f"Reconnection traceback details:\n{tb_reconnect}")


if __name__ == "__main__":
    logging.info("Starting Pakakumi Scraper")
    logging.info("Data will be saved to PostgreSQL database")

    try:
        scrape_data()
    except KeyboardInterrupt:
        logging.warning("Scraper stopped by user (KeyboardInterrupt)")
    except Exception as e:
        # Catch any unexpected errors with full traceback
        logging.error("Unexpected error in scraper", exc_info=True)
        tb = traceback.format_exc()
        logging.debug(f"Traceback details:\n{tb}")
    finally:
        driver.quit()
        logging.info("WebDriver closed")

