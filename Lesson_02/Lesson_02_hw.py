import csv
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

''' ЗАДАНИЕ:
Необходимо собрать информацию о вакансиях на вводимую должность 
(используем input или через аргументы получаем должность) с сайтов HH(обязательно) 
и/или Superjob(по желанию).
Приложение должно анализировать несколько страниц сайта (также вводим через input 
или аргументы). Получившийся список должен содержать в себе минимум:
1. Наименование вакансии.
2. Предлагаемую зарплату (разносим в три поля: минимальная и максимальная и валюта.
цифры преобразуем к цифрам).
3. Ссылку на саму вакансию.
4. Сайт, откуда собрана вакансия.
5. По желанию можно добавить ещё параметры вакансии (например, работодателя и расположение).
Структура должна быть одинаковая для вакансий с обоих сайтов.
Общий результат можно вывести с помощью dataFrame через pandas.
Сохраните в json либо csv.'''

current_career = 'voditel'
# career = 'vrach'
current_location = 'sevastopol'
# current_location = 'moskva'

current_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 '
                                 '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 OPR/81.0.4196.54 '
                                 '(Edition Yx)'}

''' Setting the pandas settings '''
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

''' Individual settings for each site '''
settings_sj = {'search_url': 'superjob.ru/vacancy/search/?keywords=', 'url': 'superjob.ru/vakansii/',
               'extension': '.html', 'result': {'class', 'f-test-search-result-item'},
               'next_page': {'class': 'icMQ_ bs_sM _3ze9n _1M2AW f-test-button-dalshe f-test-link-Dalshe'},
               'vacancy_info': '._6AfZ9', 'employer': '.f-test-text-vacancy-item-company-name',
               'city': ['span', {'class': 'f-test-text-company-item-location'}],
               'salary': {'class': 'f-test-text-company-item-salary'}}
settings_hh = {
    'search_url': 'hh.ru/search/vacancy?clusters=true&area=130&ored_clusters=true&enable_snippets=true&salary=&text=',
    'url': 'hh.ru/vacancies/', 'extension': '', 'result': {'class', 'vacancy-serp-item'},
    'next_page': {'data-qa': 'pager-next'},
    'vacancy_info': '.bloko-link', 'employer': '.vacancy-serp-item__meta-info-company',
    'city': ['div', {'data-qa': 'vacancy-serp__vacancy-address'}],
    'salary': {'data-qa': 'vacancy-serp__vacancy-compensation'}}


def ask_user_about_vacancy():
    result = input(f'Введите интересующую профессию.\nЕсли вы хотите отказаться от выбора, нажмите Enter, будут'
                   f' найдены вакансии для профессии {current_career}: ')
    return result


def get_data(career, location, headers, settings, user_responce):
    """ Main function """

    if user_responce:
        users_career = user_responce
        url = settings['search_url']
        response = requests.get(f'https://{location}.{url}' + users_career, headers=headers)
    else:
        url, extension = settings['url'], settings['extension']
        response = requests.get(f'https://{location}.{url}' + career + extension, headers=headers)

    url_name = url.split('/')[0]
    job_openings, next_page = get_resultset(response, settings)
    vacancies_list = []

    while job_openings is not None:
        for vacancy in job_openings:
            vacancies_data = {}
            vacancy_info = vacancy.select_one(settings['vacancy_info'])
            if vacancy_info:
                title = vacancy_info.text
            else:
                continue

            link = vacancy_info.get('href')
            employer = vacancy.select_one(settings['employer']).text.replace('\xa0', ' ')
            city = vacancy.find(settings['city'][0], settings['city'][1]).text.split('• ')[-1]
            min_val, max_val, currency = get_salary_data(vacancy, settings, url_name)

            vacancies_data['title'] = title
            vacancies_data['min_val'] = min_val
            vacancies_data['max_val'] = max_val
            vacancies_data['currency'] = currency

            if url_name == 'hh.ru':
                vacancies_data['link'] = f'{link}'
            else:
                vacancies_data['link'] = f'https://{location}.{url_name}{link}'

            vacancies_data['site'] = url_name
            vacancies_data['employer'] = employer
            vacancies_data['city'] = city

            # уникальная строка из id вакансии на соответствующем сайте и наименования сайта
            uniq_str = str(re.split('\D{3,}', link)[1]) + url_name
            vacancies_data['uniq_key'] = uniq_str

            vacancies_list.append(vacancies_data)

        try:
            url = f'https://{location}.{url_name}{next_page.get("href")}'
            response = requests.get(url, headers=headers)
            job_openings, next_page = get_resultset(response, settings)
        except Exception:
            break

    return vacancies_list


def get_resultset(responce, settings):
    """ Get a resultset containing all vacancies objects on current page"""

    dom = BeautifulSoup(responce.text, 'html.parser')
    result = dom.find_all('div', settings['result'])
    next_page = dom.find('a', settings['next_page'])
    return result, next_page


def get_salary_data(item, settings, url_name):
    """Universal function for getting salary data"""
    try:
        salary = item.find('span', settings['salary'])
        if url_name == 'hh.ru':
            salary = salary.text.replace('\u202f', ' ').split(' ')
        else:
            salary = salary.text.split('\xa0')
        currency = salary[-1].split('/')[0]

        if '–' in salary or '—' in salary:
            min_val = int(salary[0] + salary[1])
            max_val = int(salary[3] + salary[4])
        else:
            if 'от' in salary:
                min_val = int(salary[1] + salary[2])
                max_val = None
            elif 'до' in salary:
                min_val = None
                max_val = int(salary[1] + salary[2])
            else:
                one_salary = int(salary[0] + salary[1])
                min_val, max_val = one_salary, one_salary
    except Exception:
        min_val, max_val, currency = None, None, None
    return min_val, max_val, currency


users_responce = ask_user_about_vacancy()

all_vacancies_list = get_data(current_career, current_location, current_headers, settings_hh, users_responce) + \
                     get_data(current_career, current_location, current_headers, settings_sj, users_responce)

df_result = pd.DataFrame(all_vacancies_list)
# print(df_result)

with open("vacancies.csv", mode="w", encoding='utf-8') as wf:
    names = ['title', 'min_val', 'max_val', 'currency', 'link', 'site', 'employer', 'city', 'uniq_key']
    file_writer = csv.DictWriter(wf, delimiter=",",
                                 lineterminator="\r", fieldnames=names)
    file_writer.writeheader()
    for i in all_vacancies_list:
        file_writer.writerow(i)
