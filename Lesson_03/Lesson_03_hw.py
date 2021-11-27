from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from Lesson_02 import Lesson_02_hw

"""
Задания:
1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию, 
которая будет добавлять только новые вакансии/продукты в вашу базу.
2. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой 
больше введённой суммы (необходимо анализировать оба поля зарплаты).
"""
# создаем клиента и подключаемся к серверу
client = MongoClient('127.0.0.1', 27017)
db = client['test_vacancies']
collection = db.test_collection


# collection.drop()


def add_new_docs(some_list, some_counter, error_list):
    """Function adds to database data directly"""
    for item in some_list:
        try:
            collection.insert_one(item)
            some_counter += 1
        except DuplicateKeyError:
            # недобавленные записи помещаются в список
            error_list.append(item)
    return some_counter


def add_only_new_data():
    """Main function adds to database only new data"""
    vacancies = Lesson_02_hw.all_vacancies_list
    counter = 0
    error_list = []
    if collection.estimated_document_count() == 0:
        try:
            # уникальная строка будет уникальным индексом
            collection.create_index([('uniq_key', 1)], name='search_index', unique=True)
        except DuplicateKeyError as e:
            print(e)
        counter = add_new_docs(vacancies, counter, error_list)
    else:
        counter = add_new_docs(vacancies, counter, error_list)

    print(f'Добавлено {counter} записей')


def salary_higher_then(user_num):
    """Function shows vacancies with salary higher then user entered"""
    for doc in collection.find({'$or': [{'min_val': {'$gt': user_num}}, {'max_val': {'$gt': user_num}}]}):
        print(f'Вакансия: {doc["title"]}\n'
              f'Заработная плата: {doc["min_val"]}-{doc["max_val"]} руб.\n'
              f'Ссылка на вакансию: {doc["link"]}')


add_only_new_data()

# num = 150000
num = ''

while isinstance(num, str):
    num = input('Введите интересующий уровень зарплаты в числовом виде: ')
    if num.isdigit():
        num = int(num)
    else:
        print('Вы ввели не число!')

salary_higher_then(num)
