import datetime
from pprint import pprint

import requests
from lxml import html
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

"""
Задание:
Написать приложение, которое собирает основные новости с сайта на выбор:
1.news.mail.ru;
2.lenta.ru;
3. yandex-новости.

Для парсинга использовать XPath. Структура данных должна содержать:
- название источника;
- наименование новости;
- ссылку на новость;
- дата публикации.

Сложить собранные новости в БД
Минимум один сайт, максимум - все три
"""

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/95.0.4638.69 Safari/537.36 OPR/81.0.4196.60 (Edition Yx)'}

response = requests.get('https://news.mail.ru', headers=header)
dom = html.fromstring(response.text)

# складываем в множество, чтобы отсечь возможность повторов
news_items = set(dom.xpath("//div[contains(@data-counter-id,'20268335')]//@href"))
list_collector = []

for item in news_items:
    temp_dictionary = {}

    # получение дом-объекта для каждой новости
    news_response = requests.get(item, headers=header)
    item_dom = html.fromstring(news_response.text)

    temp_dictionary['name'] = item_dom.xpath('//h1/text()')[0]
    temp_dictionary['source'] = item_dom.xpath('//a[contains(@class,'
                                               '"link color_gray breadcrumbs__link")]/span/text()')[0]

    # получив строку даты публикации, преобразуем в datetime объект, чтобы в базе она хранилась в формате date
    date_time_str = item_dom.xpath('//span[contains(@class,'
                                   ' "note__text breadcrumbs__text js-ago")]'
                                   '/@datetime')[0].replace('T', ' ')
    date_time_obj = datetime.datetime.fromisoformat(date_time_str)
    temp_dictionary['date_time'] = date_time_obj

    temp_dictionary['link'] = item
    list_collector.append(temp_dictionary)

client = MongoClient('127.0.0.1', 27017)
db = client['news']
collection = db.hot_news
# collection.drop()

for i in list_collector:
    try:
        collection.update_one({'link': i['link']}, {'$set': i}, upsert=True)
    except DuplicateKeyError as e:
        print(e)

for doc in collection.find():
    pprint(doc)
    # для подтверждения, что дата и время публикации корректно хранятся в базе, тк
    # вывод этого поля в общем потоке некорректный:
    print(doc['date_time'])
