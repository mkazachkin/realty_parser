'''
REPAON: REalty PArser ONe
Парсинг сайта объявлений о продаже недвижимости 167000.ru
'''
from io import BytesIO
from PIL import Image
from time import sleep
from bs4 import BeautifulSoup
from keyring import get_password
from keyring import set_password
from getpass import getpass
from uuid import uuid4
import base64
import psycopg2

# Config

# без слэша в конце
URL_ROOT = 'http://167000.ru'
URL_PAGE = '?page='
URL_OFFERS = 'o'

SLEEP_TIME = 0.0

# исполняемый файл драйвера браузера для Selenium
DRIVER_CHROME_PATH = 'chromedriver'
# слэш в конце нужен
SCRSHOT_PATH = './screenshots/'
# 0, если не нужна обрезка
SCRSHOT_WIDTH = 1280
# 0, если не нужна обрезка
SCRSHOT_HEIGHT = 0
SCRSHOT_USE_JPG = True
SCRSHOT_QUAL = 51

PG_USER = 'Kaz_MYu'
# Назавние сервиса в keyring, где хранится пароль
PG_PASS_KEY = 'market_db'

PG_HOST = '192.168.1.2'
PG_PORT = '5432'
PG_DB = 'market_komi'

REGIONS = (
    'syktyvkar-i-prigorody',
    'syktyvkar',
    'syktyvdinskiy-rayon',
    'kortkerosskiy-rayon',
    'ust-vymskiy-rayon',
    'sysolskiy-rayon',
    'pechora',
    'knyazhpogostskiy-rayon',
    'koygorodskiy-rayon'
)
TYPES_REALTY = (
    'zhilaya-nedvizhimost',
    'kommercheskaya',
    'dacha',
    'uchastok',
    'garazh'
)
TYPES_OFFER = (
    'prodam',
    'sdam'
)

# Constants

REALTY_RESIDENTAL = 0
REALTY_COMMERCE = 1
REALTY_DACHAS = 2
REALTY_LANDS = 3
REALTY_GARAGES = 4

OFFER_SALE = 0
OFFER_RENT = 1

# Methods


def get_offer_ids_w_prices(
        browser_driver,
        region,
        realty_code,
        offer_code,
        f_page=1,
        l_page=1) -> list():
    '''
    Возвращает список идентификаторов объявлений о продаже и цен в районе. Парсит все страницы
    от начальной до конечной. Если конечная страница не указана (или указана равной 1), то
    конечная страница определяется автоматически.
    Аргументы
        browser_driver  ссылка на драйвер браузера
        region          название района объявлений о продаже недвижимости
        realty_code     индекс вида недвижимости из кортежа REALTY_TYPES
        offer_code      индекс вида сделки из кортежа OFFER_TYPES
        f_page          начальная страница парсинга (опционально)
        l_page          конечная страница парсинга (опционально)
    Вовращает
        get_flats_offer_ids:    список идентификаторов объявлений, список цен
    '''
    t_offer = TYPES_OFFER[offer_code]
    t_realty = TYPES_REALTY[realty_code]
    url = f'{URL_ROOT}/{region}/{t_offer}/{t_realty}/{URL_PAGE}{f_page}'
    browser_driver.get(url)
    soup = BeautifulSoup(browser_driver.page_source, features='lxml')
    if l_page == 1:
        l_page = get_last_page(soup)
    if f_page == l_page:
        return get_ids_w_prices(soup)
    else:
        sleep(SLEEP_TIME)
        return get_ids_w_prices(soup) + get_offer_ids_w_prices(
            browser_driver,
            region,
            realty_code,
            offer_code,
            f_page + 1,
            l_page)


def get_ids_w_prices(soup) -> list():
    '''
    Извлекает идентификаторы и цены предложений со страницы.
    Аргументы
        soup    обработанная библиотекой BeautifulSoup страница сайта
    Возвращает
        get_ids список идентификаторов (ключ) и цены (значения)
    '''
    ids = [tag['id'].strip('ofer- ')            # от идентификатора убираем префикс, но оставляем его строкой
           for tag in soup.select('a[id]') if tag]
    prc = [tag.string
           for tag in soup.select('td._price.offer-tablecell') if tag]
    for i in range(len(prc)):
        prc[i] = prc[i].replace(' ', '')
        prc[i] = prc[i].replace(u'\u00A0', '')  # неразрывные пробелы utf-8
        if prc[i].isdigit():
            prc[i] = int(prc[i])
        else:
            prc[i] = 0                          # цена может быть "договорная"
    if len(ids) != len(prc):
        print('WARNING: количество предложений и цен не совпадает. Страница не обработана')
        return list()
    else:
        return [{ids[i]:prc[i]} for i in range(len(ids))]


def get_last_page(soup) -> int:
    '''
    Извлекает номер последней страницы с предложениями.
    Аргументы
        soup    обработанная библиотекой BeautifulSoup страница сайта
    Возвращает
        get_last_page   номер последней страницы с предложениями
    '''
    pages_list = [int(tag.string)
                  for tag in soup.select('a._link.paginatoritem') if tag]
    if len(pages_list) != 0:
        return max(pages_list)
    else:
        return 1


def capture_screenshot(browser_driver, file_name) -> None:
    '''
    Сохраняет скриншоты страниц, адреса которых передаются в списке.
    Требуется установленный браузер Chromium/Chrome
    Аргументы
        browser_driver  ссылка на драйвер браузера
        file_name       название файла для скриншота
    '''
    page_rect = browser_driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
    screenshot_config = {
        'captureBeyondViewport': True,
        'fromSurface': True,
        'clip':
            {'width': page_rect['contentSize']['width'],
             'height': page_rect['contentSize']['height'],
             'x': 0,
             'y': 0,
             'scale': 1},
    }
    img = Image.open(BytesIO(base64.b64decode(browser_driver.execute_cdp_cmd(
        'Page.captureScreenshot', screenshot_config)['data'])))
    width = screenshot_config['clip']['width']
    height = screenshot_config['clip']['height']
    if SCRSHOT_WIDTH != 0 and width > SCRSHOT_WIDTH:
        crop_horizontal = (width - SCRSHOT_WIDTH) // 2
    else:
        crop_horizontal = 0
    if SCRSHOT_HEIGHT != 0 and height > SCRSHOT_HEIGHT:
        crop_vertical = (height - SCRSHOT_WIDTH) // 2
    else:
        crop_vertical = 0
    img = img.crop((
        crop_horizontal,
        crop_vertical,
        width - crop_horizontal,
        height - crop_vertical))
    if SCRSHOT_USE_JPG:
        img.convert('RGB').save(SCRSHOT_PATH + file_name +
                                '.jpg', quality=SCRSHOT_QUAL)
    else:
        img.save(SCRSHOT_PATH + file_name + '.png')
    img.close


def remove_saved(ids_w_prices: list) -> list:
    '''
    Убирает из списка идентификаторов те, что ранее уже были занесены в базу данных по 
    указанной цене
    Аргументы
        ids_w_prices    список идентификаторов объявлений, полученных на сайте и цены предложений
    Возвращает
        remove_saved    список идентификаторов объявлений, ранее не обработанных или с обновленной ценой
    '''
    tmp_table = 't' + str(uuid4()).replace('-', '')
    sql_str = f"""CREATE TABLE {tmp_table} (
        offer_id uuid NOT NULL DEFAULT uuid_generate_v4(),
        offer_original_id varchar(20) NOT NULL,
        offer_price float8 NOT NULL,
        CONSTRAINT {tmp_table}_pk PRIMARY KEY (offer_id));\n"""
    sql_str += f'CREATE INDEX {tmp_table}_idx ON {tmp_table} (offer_id, offer_original_id, offer_price);'
    values = str(ids_w_prices).\
        replace('[', '').\
        replace(']', '').\
        replace('{', '(').\
        replace('}', ')').\
        replace(': ', ',')
    sql_str += f'INSERT INTO public.{tmp_table} (offer_original_id, offer_price) VALUES ' + \
        values + ';'
    sql_str += f'DELETE FROM {tmp_table} tmt USING t_offers tof ' + \
        'WHERE tmt.offer_original_id=tof.offer_original_id and tmt.offer_price=tof.offer_price;'
    sql_execute(sql_str)
    sql_str = f"SELECT offer_original_id FROM {tmp_table};"
    record_list = [row[0] for row in sql_execute(sql_str)]
    sql_str = f'DROP TABLE {tmp_table};'
    sql_execute(sql_str)
    return record_list


def sql_execute(sql_str) -> list:
    '''
    Выполняет SQL запрос к базе данных postgress и возвращает результаты, при их наличии
    Аргументы
        sql_str         SQL выражение
    Возвращает
        sql_execute     список значений, полученных от запроса
    '''
    passwd = get_password(PG_PASS_KEY, PG_USER)
    connection = psycopg2.connect(
        user=PG_USER,
        password=passwd,
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB)
    cursor = connection.cursor()
    cursor.execute(sql_str)
    connection.commit()
    record_list = cursor.fetchall() if cursor.rowcount > 0 else list()
    cursor.close()
    connection.close()
    return record_list


def set_db_password() -> None:
    '''
    Сохраняет пароль пользователя в конфигурацию
    '''
    set_password(PG_PASS_KEY, PG_USER, getpass())
