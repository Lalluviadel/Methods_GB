import pandas as pd
import requests
from bs4 import BeautifulSoup

from append_to_excel import append_df_to_excel
from my_data import login, password


def give_me_my_hometasks():
    headers_auth = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 OPR/81.0.4196.54 '
                                  '(Edition Yx)'}

    response_auth = requests.post('https://riso.sev.gov.ru/ajaxauthorize',
                                  data={'username': login, 'password': password, 'return_uri': '/'},
                                  headers=headers_auth)

    headers_hw = {'Cookie': 'school_domain=sevschool31; '
                            'session_id=157cc524e49a26bb6436d0fea037496b; '
                            'csrf-token-name=csrftoken; '
                            'csrf-token-value=16bb31b742eb37ce66e7ddc8f9860cc788b4d4fdcc5ac8673789e7bf863d2af9dea7cb7e0345b85e',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                'Chrome/95.0.4638.69 Safari/537.36 OPR/81.0.4196.60 (Edition Yx)'}

    hw_list = []
    hw_res_cur_week = get_result('https://riso.sev.gov.ru/journal-app/u.9481', headers_hw)
    scrap_hw(hw_res_cur_week, hw_list)
    hw_res_next_week = get_result('https://riso.sev.gov.ru/journal-app/u.9481/week.-1', headers_hw)
    scrap_hw(hw_res_next_week, hw_list)

    flag = 0
    for i in hw_list:
        df_result = pd.DataFrame(i)
        if flag == 0:
            with pd.ExcelWriter('Урочки.xlsx', engine='xlsxwriter') as wb:
                df_result.to_excel(wb, sheet_name=list(i)[0])
            flag += 1
        else:
            append_df_to_excel('Урочки.xlsx', df_result, sheet_name=list(i)[0])


def get_result(url, headers):
    response_homeworks = requests.get(url, headers=headers)
    dom_hw = BeautifulSoup(response_homeworks.text, 'html.parser')
    result_hw = dom_hw.find_all('div', {'class': 'dnevnik-day'})
    return result_hw


def scrap_hw(result, main_list):
    for item in result:
        hw_data = {}
        day_name = item.select_one('.dnevnik-day__title').text.strip('\n ')
        lessons = item.find_all('div', {'class': 'dnevnik-lesson'})

        if lessons:
            hw_day_data = {}
            for lesson in lessons:
                subject = lesson.select_one('.js-rt_licey-dnevnik-subject').text
                task = lesson.select_one('.dnevnik-lesson__task')
                if task:
                    task = task.text.strip('\n ').split('\n')[0]
                else:
                    task = '-'
                hw_day_data[subject] = task
            hw_data[day_name] = hw_day_data
            main_list.append(hw_data)

# give_me_my_hometasks()
