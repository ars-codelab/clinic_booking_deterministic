import os
import json
import time
from datetime import datetime, time as dt_time
import pytz

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# --- Configuration ---
CONFIG_FILE = 'config.json'
WEBSITE_URL = "https://yoyaku.atlink.jp/matsunobu/login"
JST = pytz.timezone('Asia/Tokyo')

# --- Main Crawler Logic ---
def load_config():
    """Loads config and handles case where file might not exist."""
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def parse_time_string(time_str):
    time_str = time_str.strip().upper()
    if time_str.startswith('AM') or time_str.startswith('PM'):
        return datetime.strptime(time_str, '%p%I:%M').time()
    return None

def is_in_preferred_range(slot_time, preferred_ranges):
    if not slot_time: return False
    for r in preferred_ranges:
        start_str, end_str = r.split(' - ')
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        if start_time <= slot_time < end_time:
            return True
    return False

def wait_for_reservation_opening(driver, wait, is_scheduled_run):
    """Waits for slots if it's a scheduled run, otherwise checks immediately."""
    print("Step 8: Checking for reservation slots...")
    
    if is_scheduled_run:
        opening_time = dt_time(6, 0, 0)
        timeout_time = dt_time(6, 5, 0)
        now_jst_dt = datetime.now(JST)

        if now_jst_dt.time() < opening_time:
            wait_seconds = (datetime.combine(now_jst_dt.date(), opening_time) - now_jst_dt).total_seconds()
            if wait_seconds > 0:
                print(f"Scheduled run: Waiting for {wait_seconds:.0f} seconds until 6:00 AM JST...")
                time.sleep(wait_seconds)

        while datetime.now(JST).time() < timeout_time:
            try:
                driver.find_element(By.XPATH, "//tbody/tr[position()=2 or position()=3]/td[1]/a")
                print("Reservation slots are open!")
                return True
            except NoSuchElementException:
                print(f"Slots not yet open at {datetime.now(JST).strftime('%H:%M:%S')}. Refreshing...")
                time.sleep(10)
                driver.refresh()
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
        
        print("Scheduled run timeout reached (6:05 AM JST). No reservation slots found.")
        return False
    else: # This is a "Run Now" request
        try:
            driver.find_element(By.XPATH, "//tbody/tr[position()=2 or position()=3]/td[1]/a")
            print("'Run Now': Found available appointment blocks.")
            return True
        except NoSuchElementException:
            print("'Run Now': No immediate appointment blocks are available. The clinic may be closed.")
            return False

def attempt_to_book_slot(driver, wait, config):
    print("Step 9: Searching for an available time slot...")
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form[name='tmform']")))
        for slot in driver.find_elements(By.CSS_SELECTOR, "form[name='tmform']"):
            try:
                time_str = slot.find_element(By.CSS_SELECTOR, ".tm-selok").text
                if is_in_preferred_range(parse_time_string(time_str), config['preferred_time_ranges']):
                    print(f"SUCCESS: Found matching slot {time_str}. Clicking to book.")
                    slot.find_element(By.CSS_SELECTOR, "a.tm-kakoi").click()
                    return True
            except (NoSuchElementException, ValueError): continue
        return False
    except TimeoutException: return False

def run_automation():
    config = load_config()

    # --- Conditional Run Check ---
    if not config:
        print("Config file not found or is empty. Exiting.")
        return

    request_date_str = config.get("request_date")
    today_jst_str = datetime.now(JST).strftime('%Y-%m-%d')
    
    if request_date_str != today_jst_str:
        print(f"No booking request found for today ({today_jst_str}). Request was for {request_date_str}. Exiting.")
        return
      
    print(f"Booking request found for {today_jst_str}. Proceeding...")
    
    # Determine if this is a scheduled run (around 5:58 AM) or an immediate "Run Now"
    now_jst_time = datetime.now(JST).time()
    is_scheduled_run = dt_time(5, 57) <= now_jst_time <= dt_time(6, 5)

    driver = get_webdriver()
    wait = WebDriverWait(driver, 10)
    
    try:
        # Steps 1-7
        print("Executing Steps 1-7: Login and initial navigation...")
        driver.get(WEBSITE_URL)
        wait.until(EC.presence_of_element_located((By.NAME, "logonid"))).send_keys(config['credentials']['username'])
        driver.find_element(By.NAME, "cpasswd").send_keys(config['credentials']['password'])
        driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='ログイン']").click()
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "予約登録"))).click()
        wait.until(EC.element_to_be_clickable((By.ID, "deptgr25"))).click()
        wait.until(EC.element_to_be_clickable((By.ID, "obj505"))).click()
        driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='次　へ']").click()
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='内容を確認の上、次画面へ進む']"))).click()
        print("Steps 1-7 complete.")

        # Step 8
        if not wait_for_reservation_opening(driver, wait, is_scheduled_run): return

        # The rest of the booking logic
        check_morning = any(int(r.split(':')[0]) < 13 for r in config['preferred_time_ranges'])
        check_afternoon = any(int(r.split(':')[0]) >= 13 for r in config['preferred_time_ranges'])
        booked = False

        if check_morning:
            try:
                driver.find_element(By.XPATH, "//tbody/tr[2]/td[1]/a").click()
                if attempt_to_book_slot(driver, wait, config): booked = True
                else: driver.back(); wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
            except NoSuchElementException: print("Morning block not available.")
        
        if not booked and check_afternoon:
            try:
                driver.find_element(By.XPATH, "//tbody/tr[3]/td[1]/a").click()
                if attempt_to_book_slot(driver, wait, config): booked = True
            except NoSuchElementException: print("Afternoon block not available.")

        if not booked: return

        # Steps 10-11
        wait.until(EC.presence_of_element_located((By.NAME, "deccm32__200"))).send_keys(config['patient_name'])
        driver.find_element(By.NAME, "deccm32__245").send_keys(config['symptoms'])
        driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='次　へ']").click()
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[value='予約の登録']"))).click()
        time.sleep(5)
        print("\n--- RESERVATION COMPLETE! ---")

    finally:
        if 'driver' in locals() and driver:
            print("Closing WebDriver.")
            driver.quit()

if __name__ == "__main__":
    run_automation()
