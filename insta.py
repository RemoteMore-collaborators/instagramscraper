import time
import csv
import re
import gspread

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, JavascriptException, StaleElementReferenceException
from oauth2client.service_account import ServiceAccountCredentials
from utils import custom_logger, paste_csv_to_wks, is_in_english

CURRENT_DIR = '/home/ubuntu/instagramscraper'
# CURRENT_DIR = '.'
BIN_DIR = '/usr/bin'
# BIN_DIR = '.'
PAUSE_TIME = 3

chrome_options = Options()
chrome_options.add_argument("--headless")

current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

logfile = f"{CURRENT_DIR}/logs/insta_{current_time}.log"
logger = custom_logger(logfile)

logger.info(f"Logfile name {logfile}")

driver_path = f'{BIN_DIR}/chromedriver'
driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
driver.set_script_timeout(300)

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

logger.info(f"Clicking through posts and writing comments data to {csv_path}...")
post_n = 1
while True:
    if post_n > 30:
        break
    time.sleep(PAUSE_TIME)
    scroll_to_top = 0
    while True:
        logger.info("Scrolling to the top")

        time.sleep(1)
        try:
            post_link_ = driver.find_element_by_class_name("c-Yi7").get_attribute('href')
                   
            if post_link_ == "https://www.instagram.com/p/B55sWs_gu1e/":
                logger.info("currently on video post")
                if scroll_to_top > 10:
                    logger.info("Breaking out of the loop")
                    raise JavascriptException
                else:
                    scroll_to_top += 1
                    
            driver.execute_script(
                'document.querySelector("div.eo2As > div.EtaWk > ul > li > div > button > span").scrollIntoView();')
        except JavascriptException as err:
            logger.error("JS error")
            try:
                post_link_ = driver.find_element_by_class_name("c-Yi7").get_attribute('href')
                if post_link_ == "https://www.instagram.com/p/B55sWs_gu1e/":
                    raise Exception
                
                more_comments = "//span[@aria-label='Load more comments']"
                button = driver.find_element_by_xpath(more_comments)
                ActionChains(driver).move_to_element(button).click(button).perform()
            except:
                logger.info("No more paginated comments")
                break

        try:
            more_comments = "//span[@aria-label='Load more comments']"
            ActionChains(driver).move_to_element(driver.find_element_by_xpath(more_comments)).click().perform()
            time.sleep(0.05)
        except StaleElementReferenceException as er:
            logger.error("StaleElementReferenceException")
            pass
        except NoSuchElementException:
            logger.error("No such element exception")
            pass

    with open(csv_path, 'a+', encoding='utf-8') as csv_file:
        fileWriter = csv.writer(csv_file, dialect='excel')
        try:
            post_block = driver.find_element_by_css_selector('li.gElp9.rUo9f.PpGvg div.C4VMK')
        except NoSuchElementException as err:
            logger.error("No such element exception on post block")
            time.sleep(1)
            post_block = driver.find_element_by_css_selector('li.gElp9.rUo9f.PpGvg div.C4VMK')

        post_author_ = post_block.find_element_by_class_name("_6lAjh").text.strip()
        post_author = " ".join(post_author_.split())
        post_content_ = post_block.find_element_by_xpath('//h2[@class="_6lAjh "]/following-sibling::span').text.strip()
        post_content = " ".join(post_content_.split())
        date_time = post_block.find_element_by_xpath('//time[@class="FH9sR Nzb55"]').get_attribute('datetime').replace(".000Z", "").replace("T", " ")
        link = driver.find_element_by_class_name("c-Yi7").get_attribute('href')

        likes = ""
        try:
            video_views_ = driver.find_element_by_class_name("vcOH2")
            likes = video_views_.text
        except NoSuchElementException:
            pass

        try:
            photo_likes_ = driver.find_element_by_class_name("Nm9Fw")
            likes = photo_likes_.text
        except NoSuchElementException:
            pass

        fileWriter.writerow([post_author, post_content, date_time, likes, link])

        comment_blocks = driver.find_elements_by_xpath("//ul[@class='Mr508']")
        comment_n = 1
        
        for comment in comment_blocks:
            try:
                comment_text = comment.find_element_by_xpath("./div/li/div/div/div[2]/span").text

                if not is_in_english(comment_text):
                    logger.info(f"{comment_text} is not english")
                    continue

                from_user = comment.find_element_by_xpath("./div/li/div/div/div[2]/h3/a").text

                date_time_obj = comment.find_element_by_xpath("./div/li/div/div/div[2]/div/div/time").get_attribute(
                    'datetime').replace(".000Z", "").replace("T", " ")
                likes_ = comment.find_element_by_xpath("./div/li/div/div/div[2]/div/div/button[1]").text
                if 'Reply' not in likes_:
                    likes = likes_
                else:
                    likes = "0 likes"

                hash_tags_element = ''
                hash_tags_content = comment.find_elements_by_xpath("./div/li/div/div/div[2]/span/a")

                for hash_tag in hash_tags_content:
                    if "#" in hash_tag.text:
                        hash_tags_element = hash_tags_element + hash_tag.text + " "

                try:
                    replies_ = comment.find_element_by_class_name("EizgU").text
                    replies = re.findall(r'\b\d+\b', replies_)
                    if replies:
                        replies = int(replies[0])
                except NoSuchElementException:
                    replies = 0

                logger.info(f"Parsing comment {comment_n}")
                comment_n += 1

            except StaleElementReferenceException as err:
                try:
                    comment = driver.find_elements_by_xpath(f"//ul[@class='Mr508'][position()={comment_n}]")[0]
                except:
                    pass

            line = [from_user, comment_text, date_time_obj, likes, replies, hash_tags_element]
            fileWriter.writerow(line)

        fileWriter.writerow(['', '', '', '', ''])
        logger.info(f"Moving to post {post_n + 1}")
        post_n += 1

    try:
        next_btn = driver.find_element_by_xpath("//a[@class='HBoOv coreSpriteRightPaginationArrow']")
        next_btn.click()
    except NoSuchElementException as err:
        print(err)
        break

driver.quit()

logger.info(f"Clicking through posts and writing comments data to {csv_path} file complete!")

logger.info('Write csv content to "Scraping task instagram" googlesheet')

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(f'{CURRENT_DIR}/instagramscraper.json', scope)

gc = gspread.authorize(credentials)
wks = gc.open("Scraping task instagram")
paste_csv_to_wks(csv_path, wks, 'A2', logger)

logger.info("Writing complete!")
