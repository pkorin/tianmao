import re
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)

def search():
    try:
        browser.get('https://www.jd.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#key"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#search > div > div.form > button"))
        )

        input.send_keys('美食')
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#J_bottomPage > span.p-skip > em:nth-child(1) > b")))
        get_products()
        return total.text
    except TimeoutException:
        return search()

def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[@id=\"J_bottomPage\"]/span[2]/input"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id=\"J_bottomPage\"]/span[2]/a"))
        )
        #browser.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#J_bottomPage > span.p-num > a.curr'),str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_goodsList .gl-warp .gl-item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#J_goodsList .gl-warp .gl-item').items()
    for item in items:
        product = {
            'image':item.find('.p-img *').attr('src'),
            'price':item.find('.p-price').text()[2:],
            'deal':item.find('.p-commit').text()[:-4],
            'title':item.find('.p-tag').text(),
            'shop':item.find('.curr-shop').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到mongodb成功',result)
    except Exception:
        print('存储到MongoDb失败',result)

def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    print(total)
    for i in range(2,total + 1):
        time.sleep(2)
        next_page(i)
    browser.close()

if __name__ == '__main__':
    main()
