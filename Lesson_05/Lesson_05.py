import datetime as dt
import locale
import time
from pprint import pprint

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

"""
Задание:
Вариант II
2) Написать программу, которая собирает товары «В тренде» с сайта техники mvideo и складывает данные в БД. Сайт можно
выбрать и свой. Главный критерий выбора: динамически загружаемые товары
"""

chrome_options = Options()
chrome_options.add_argument('start-maximized')

driver = webdriver.Chrome("./chromedriver.exe", options=chrome_options)
driver.get("https://www.mvideo.ru")
driver.implicitly_wait(10)

anchor_for_scrolldown = driver.find_element(By.CLASS_NAME, 'ng-tns-c268-2')
# прокрутка на 1500 px вниз для подзагрузки нужной нам области
if anchor_for_scrolldown:
    driver.execute_script("window.scrollTo(0, 1500)")

trends_button = driver.find_element(By.XPATH, "//span[contains(text(), 'В тренде')]/ancestor::*[2]")
try:
    trends_button.click()
except Exception as e:
    print(e)

product_cards = driver.find_element(By.CSS_SELECTOR, 'mvid-product-cards-group')
product_names = product_cards.find_elements(By.CLASS_NAME, 'product-mini-card__name')
product_prices = product_cards.find_elements(By.CLASS_NAME, 'product-mini-card__price')
# объединяем полученные списки с найденными объектами
product_data = list(zip(product_names, product_prices))

result_list = []

for product in product_data:
    product_dict = {'name': product[0].text,
                    'link': product[0].find_element(By.XPATH, ".//a").get_attribute('href'),
                    'price': int(product[1].find_element(By.CLASS_NAME, 'price__main-value').text.replace(' ', ''))}
    result_list.append(product_dict)

client = MongoClient('127.0.0.1', 27017)
db = client['products']
collection = db.trend_products
# collection.drop()

for i in result_list:
    try:
        collection.update_one({'link': i['link']}, {'$set': i}, upsert=True)
    except DuplicateKeyError as e:
        print(e)

# распечатка документов коллекции с трендами М-Видео
for doc in collection.find():
    pprint(doc)

"""
Задание:
Вариант I
Написать программу, которая собирает входящие письма из своего или тестового почтового ящика и сложить данные
о письмах в базу данных (от кого, дата отправки, тема письма, текст письма полный)
Логин тестового ящика: study.ai_172@mail.ru
Пароль тестового ящика: NextPassword172#
"""
# установим локаль так, чтобы применились российские настройки, это потребуется ниже
locale.setlocale(locale.LC_ALL, 'ru')

driver.get('https://mail.ru/')
form = driver.find_element(By.CSS_SELECTOR, 'form')
email_input = form.find_element(By.CLASS_NAME, 'email-input')
email_input.send_keys('study.ai_172@mail.ru')
email_button = form.find_element(By.CSS_SELECTOR, 'button')
email_button.click()

# ждем, пока кнопка подтверждения пароля не станет кликабельной
wait = WebDriverWait(driver, 10)
password_button = wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'second-button')))

password_input = form.find_element(By.XPATH, '//div[contains(@class, "password-input-container")]/input')
password_input.send_keys('NextPassword172#')
password_button.click()

driver.implicitly_wait(10)

last_letter = 0
link_collector = set()
while True:
    data = driver.find_element(By.CLASS_NAME, 'letter-list')
    letters = data.find_elements(By.CSS_SELECTOR, 'a')

    # когда объект последнего письма будет соответствовать последнему элементу
    # подгруженного списка писем, прекращаем цикл
    if letters[-1] == last_letter:
        break

    # забираем во множество все ссылки, отсекая повторные
    for i in letters:
        link = i.get_attribute('href')
        # рекламные ссылки не забираем
        if link and 'e.mail.ru' in link:
            link_collector.add(link)

    last_letter = letters[-1]
    actions = ActionChains(driver)
    actions.move_to_element(letters[-1])
    actions.perform()

    time.sleep(1)


# pprint(link_collector)

def give_me_correct_date(date):
    """Функция нужна для преобразования кривых дат из письма, вида:
    # date = 'Вчера, 0:35'
    # date = '3 декабря, 18:21'
    к UTC-формату datetime, который MongoDB будет хранить в формате Date, а не строчном
    """
    if 'Вчера' in date:
        # делим строку c данными даты письма на составляющие
        time_l = date.split(', ')[1].split(":")
        # получаем вчерашнюю дату
        tomorrow = (dt.datetime.now() - dt.timedelta(days=1))
        # объединяем и получаем корректную дату
        letter_datetime = tomorrow.replace(hour=int(time_l[0]), minute=int(time_l[1])).replace(second=0, microsecond=0)
    else:
        # делим строку c данными даты письма на составляющие
        date_parts = date.split(' ')
        # сокращаем словесное обозначение месяца до 3 букв
        date_parts[1] = date_parts[1][:3]
        # май пришлось принудительно
        if date_parts[1] == 'мая':
            date_parts[1] = 'май'
        # получаем текущий год
        date_parts.append(dt.datetime.today().strftime('%Y'))
        # объединяем все элементы в строку
        date_str = " ".join(date_parts)
        # настроенная ранее локаль позволит форматировать строку в корректную дату
        letter_datetime = dt.datetime.strptime(date_str, '%d %b %H:%M %Y')
    return letter_datetime


result_list = []
# проходимся по коллекции собранных ссылок на письма
for i in link_collector:
    driver.get(i)
    letters_dict = {}

    elem = driver.find_element(By.CLASS_NAME, 'letter__author')
    letters_dict['author'] = elem.find_element(By.CLASS_NAME, 'letter-contact').text
    raw_date = elem.find_element(By.CLASS_NAME, 'letter__date').text
    letters_dict['date'] = give_me_correct_date(raw_date)

    letters_dict['link'] = i
    letters_dict['thread'] = driver.find_element(By.CLASS_NAME, 'thread__subject').text
    letters_dict['text'] = driver.find_element(By.CLASS_NAME, 'letter__body').text
    result_list.append(letters_dict)

client = MongoClient('127.0.0.1', 27017)
db = client['mail']
collection = db.letters
# collection.drop()

for i in result_list:
    try:
        collection.update_one({'link': i['link']}, {'$set': i}, upsert=True)
    except DuplicateKeyError as e:
        print(e)

# for doc in collection.find():
#     pprint(doc)
