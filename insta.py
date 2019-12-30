import time
import csv
import re
import gspread

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from utils import custom_logger, paste_csv_to_wks

# CURRENT_DIR = '/home/ubuntu/instascraper'
CURRENT_DIR = '.'
# BIN_DIR = '/usr/bin'
BIN_DIR = '.'
PAUSE_TIME = 3

chrome_options = Options()
chrome_options.add_argument("--headless")

current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

logfile = f"{CURRENT_DIR}/logs/insta_{current_time}.log"
logger = custom_logger(logfile)

logger.info(f"Logfile name {logfile}")

driver_path = f'{BIN_DIR}/chromedriver'
driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)

logger.info("Loading page...")

driver.get("https://www.instagram.com/candycrushsaga/")

logger.info("Page loaded!")

logger.info("Scrolling through the page...")

while True:
    last_height = driver.execute_script("return document.body.scrollHeight/8;")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/8);")
    time.sleep(PAUSE_TIME)
    new_height = driver.execute_script("return document.body.scrollHeight/8;")
    if new_height == last_height:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/8);")
        time.sleep(PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight/8;")
        if new_height == last_height:
            break
        else:
            last_height = new_height
            continue

logger.info("Done scrolling through the page...")

elements = driver.find_elements_by_xpath("//div[@class='v1Nh3 kIKUG  _bz0w']")
elements[0].click()
time.sleep(PAUSE_TIME)

csv_path = f"{CURRENT_DIR}/csv/insta_{current_time}.csv"
fp = open(csv_path, "w")
wr = csv.writer(fp, dialect='excel')
wr.writerow(['from_user', 'text', 'time', 'likes', 'hashtag'])

logger.info(f"Clicking through posts and writing comments data to {csv_path}...")

while True:
    time.sleep(PAUSE_TIME)
    try:

        next_btn = driver.find_element_by_xpath("//a[@class='HBoOv coreSpriteRightPaginationArrow']")
        comment_blocks = driver.find_elements_by_xpath("//ul[@class='Mr508']")

        for comment in comment_blocks:
            line = []
            from_user = comment.find_element_by_xpath("./div/li/div/div/div[2]/h3/a").text
            line.append(from_user)

            text = comment.find_element_by_xpath("./div/li/div/div/div[2]/span").text
            text = BeautifulSoup(text, "lxml").text
            cleaner = re.compile('<.*?>')
            cleaned_text = re.sub(cleaner, '', text)
            line.append(cleaned_text)

            time_element = comment.find_element_by_xpath("./div/li/div/div/div[2]/div/div/time").get_attribute('datetime')
            line.append(time_element)

            likes = comment.find_element_by_xpath("./div/li/div/div/div[2]/div/div/button[1]").text
            if 'Reply' not in likes:
                line.append(likes)
            else:
                line.append('')

            hash_tags_element = ''
            hash_tags_content = comment.find_elements_by_xpath("./div/li/div/div/div[2]/span/a")
            for hash_tag in hash_tags_content:
                if "#" in hash_tag.text:
                    hash_tags_element = hash_tags_element + hash_tag.text + " "
            line.append(hash_tags_element)

            wr = csv.writer(fp, dialect='excel')
            wr.writerow(line)

        next_btn.click()

    except NoSuchElementException:

        logger.info(f"Clicking through posts and writing comments data to {csv_path} file complete!")

        fp.close()

        content = open(csv_path, 'r', encoding='utf-8').read()

        logger.info('Write csv content to "Scraping task instagram" googlesheet')

        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(f'{CURRENT_DIR}/instagramscraper.json', scope)

        gc = gspread.authorize(credentials)
        wks = gc.open("Scraping task instagram")
        paste_csv_to_wks(csv_path, wks, 'A2')

        logger.info("Writing complete!")

        driver.quit()
        break
