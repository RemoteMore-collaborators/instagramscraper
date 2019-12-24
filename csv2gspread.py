import time
import csv
import re
import gspread

from _datetime import datetime
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from utils import custom_logger, paste_csv_to_wks

content = open('./csv/insta_2.csv', 'r', encoding='utf-8').read()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('./instagramscraper.json', scope)

gc = gspread.authorize(credentials)
wks = gc.open("Scraping task instagram")
paste_csv_to_wks('./csv/insta_2.csv', wks, 'A2')
