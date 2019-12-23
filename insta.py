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

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', options=chrome_options)

driver.get("https://www.instagram.com/candycrushsaga/")

pause_time = 3
while True:
    last_height = driver.execute_script("return document.body.scrollHeight/8;")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/8);")
    time.sleep(pause_time)
    new_height = driver.execute_script("return document.body.scrollHeight/8;")
    if new_height == last_height:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/8);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight/8;")
        if new_height == last_height:
            break
        else:
            last_height = new_height
            continue

time.sleep(pause_time)
elements = driver.find_elements_by_xpath("//div[@class='v1Nh3 kIKUG  _bz0w']")
elements[0].click()

csv_path = "./csv/insta_" + str(datetime.now()) + ".csv"
fp = open(csv_path, "w")
wr = csv.writer(fp, dialect='excel')
wr.writerow(['from_user', 'text', 'time', 'likes', 'hashtag'])

logger = custom_logger("./log/insta_" + str(datetime.now()))

while True:
    time.sleep(pause_time)
    try:
        next_btn = driver.find_element_by_xpath("//a[@class='HBoOv coreSpriteRightPaginationArrow']")
        time.sleep(pause_time)
        comment_blocks = driver.find_elements_by_xpath("//ul[@class='Mr508']")

        for comment in comment_blocks:
            line = []
            from_user = comment.find_element_by_xpath("./div/li/div/div/div[2]/h3/a").text
            # print("from_user: ", from_user)
            line.append(from_user)

            text = comment.find_element_by_xpath("./div/li/div/div/div[2]/span").text
            text = BeautifulSoup(text, "lxml").text
            cleaner = re.compile('<.*?>')
            cleaned_text = re.sub(cleaner, '', text)
            # print("text: ", cleaned_text)
            line.append(cleaned_text)

            time_element = comment.find_element_by_xpath("./div/li/div/div/div[2]/div/div/time").get_attribute('datetime')
            # print("time: ", time_element)
            line.append(time_element)

            likes = comment.find_element_by_xpath("./div/li/div/div/div[2]/div/div/button[1]").text
            if 'Reply' not in likes:
                # print("likes: ", likes)
                line.append(likes)
            else:
                line.append('')

            hash_tags_element = ''
            hash_tags_content = comment.find_elements_by_xpath("./div/li/div/div/div[2]/span/a")
            for hash_tag in hash_tags_content:
                if "#" in hash_tag.text:
                    hash_tags_element = hash_tags_element + hash_tag.text + " "
            # print("hashtags: ", hash_tags_element)
            line.append(hash_tags_element)

            wr = csv.writer(fp, dialect='excel')
            wr.writerow(line)

        time.sleep(pause_time)
        next_btn.click()
    except NoSuchElementException:
        fp.close()

        content = open(csv_path, 'r', encoding='utf-8').read()

        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('./instagramscraper.json', scope)

        gc = gspread.authorize(credentials)
        wks = gc.open("Instagram scraping")
        paste_csv_to_wks(csv_path, wks, 'A2')

        sleep_period = 3600

        logger.info("Script sleeping for an hour")
        time.sleep(sleep_period)
        logger.info("Sleep period ended")

        print("all success!!!!!!!!!!!!!!")
        driver.quit()
        break
