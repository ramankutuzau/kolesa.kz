import asyncio
from aiohttp import ClientSession,ClientConnectorError
from bs4 import BeautifulSoup
import requests
from time import sleep
from datetime import datetime
import re
from fake_useragent import UserAgent
import random

url_list = [""]

async def send_to_tg(text):
    send_text = 'https://api.telegram.org/bot' + '6940107238:AAH0oYf1a8p4MpzyeEJq1vQA6vdcV6AyE7Q' + \
        '/sendMessage?chat_id=' + "717945869" + '&parse_mode=HTML&text=' + text
    async with ClientSession() as session:
        async with session.get(send_text) as response:
            return await response.text()

async def send_to_tg_2(text):
    send_text = 'https://api.telegram.org/bot' + '6742172622:AAFjGwKXB2ekCQKlBBp1iury0s-81XRlvO0' + \
        '/sendMessage?chat_id=' + "5136898344" + '&parse_mode=HTML&text=' + text
    async with ClientSession() as session:
        async with session.get(send_text) as response:
            return await response.text()
    
async def search_cities_category(search_city,proxy):
    # headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0'}
    ua = UserAgent()

    headers = {'User-agent': ua.random}
    url = 'https://m.kolesa.kz/regions/all/?categoryName=auto.car'

    proxy = f"http://{proxy}"
    async with ClientSession() as session:
        async with session.get(url,headers=headers, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                for city in data:
                    if str(city['value']).lower() == search_city.lower():
                        print(city['alias'])
                        return city['alias']
            else:
                print(f'NO DATA FOR THIS CITY:{search_city}')
                return


async def fetch(url, session, params, proxy):
    try:
        ua = UserAgent()

        headers = {'User-agent': ua.random}
        # print(f' HEEEEEEEEEEEEEADERS {headers}')
        proxy = f"http://{proxy}"
        async with session.get(url,headers=headers, params=params, proxy=proxy) as response:
            response_text = await response.text()
            print(f'Запрос прошел , proxy : {proxy}')
            return response_text
    except ClientConnectorError as e:
        print(f"Failed to connect with proxy {proxy}: {e}")
        return None

def check_car_info(car):
    car_info = ""
    car_title_element = car.find(class_="a-card__title")
    if car_title_element:
        car_title = car_title_element.text.strip()  # Получаем текст с названием машины
        car_info = car_title + " "
    else:
        print("Название машины не найдено")
        return None

    car_year_element = car.find(class_="a-card-info__description-item", string=re.compile(r"\b\d{4}\b"))  # Ищем элемент с годом выпуска
    if car_year_element:
        car_year_text = car_year_element.text.strip()  # Получаем текст с годом выпуска
        car_year_match = re.search(r'\b\d{4}\b', car_year_text)  # Извлекаем только числовое значение года
        if car_year_match:
            car_year = int(car_year_match.group())  # Преобразуем год выпуска в целое число
            # print(f'Год выпуска авто: {car_year}')
            car_info += str(car_year) + ' г. '
    else:
        print("Год выпуска не найден")
        return None
    
    car_price_element = car.find(class_="a-card-price__primary")
    if car_price_element:
        car_price_text = car_price_element.text.strip()  # Получаем текст с ценой машины
        car_price = int(car_price_text.replace('\xa0', '').split('₸')[0])  # Преобразуем текст цены в число
        # print(car_price)
        car_info += " | " + str(car_price) + " T | "
    else:
        print("Цена машины не найдена")
        return None
    return (car_info,car_year)
        
cars_ids = []
async def run_parse(search_city,user_percent,user_date,proxies):
    # headers = {'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0'}
    ua = UserAgent()
    headers = {'User-agent': ua.random}
    async with ClientSession(headers=headers) as session:
        url = f"https://m.kolesa.kz/cars/{search_city}"
        params = {'auto-custom':2}
        proxy = random.choice(proxies)
        await asyncio.sleep(random.uniform(1, 3))
        html = await fetch(url, session, params,proxy)
        
        
        bs = BeautifulSoup(html, "html.parser")
        cars = bs.find_all(class_="search-list__item")
        last_car = cars[0]
 
        a = last_car.find("a")
        href = a['href']
        
        card_id = href.split('/')[-1]
        
        # Проверяем, была ли машина уже проверена
        if card_id in cars_ids:
            print(f'Машина с ID {card_id} уже была проверена. Пропускаем.')
            return
        
        print(f'card_id {card_id}')

        if(a is None) or (url_list[0] == href): return

        url_list[0] = href
        pattern = "https://m.kolesa.kz"
        card_url = f'{pattern}{href}'
        message_text = f'{card_url}"\n"'

        # print(message_text)

        car_info = check_car_info(last_car)
        if car_info == None:
            return

        # Проверка года выпуска
        car_year = car_info[1]
        if user_date >= car_year:
            print(f'Не подходит по году выпуска: {car_info[0]}')
            return
        else:
            print(f'Проверяем: {car_info}')


        await asyncio.sleep(random.uniform(1, 3))
        card_text = await fetch(card_url, session, params,proxy)
        with open("card_text.html", "w", encoding="utf-8") as file:
            file.write(card_text)
        soup = BeautifulSoup(card_text,'html.parser')
        properties_list = soup.find_all(class_='a-properties__info')

        for i in properties_list:
            values = i.find_all("div")
            name_value = values[0].text.strip()
            value = values[1].text.strip()
            message_text += f'<b>{name_value}</b> {value}\n'

        notes = soup.find('div', class_="a-block a-notes").find_all("p")
        for i in notes:
            text_note = re.sub(" +", " ", i.text).replace("\n", "")
            message_text += text_note+"\n"

        await asyncio.sleep(random.uniform(1, 3))
        price_info_url = f"https://m.kolesa.kz/a/average-price/{card_id}"

        ua = UserAgent()

        
        proxy = f"http://{proxy}"
        async with session.get(price_info_url,headers=headers,  proxy=proxy) as response:
            price_info = await response.json()

            print(f'Запрос на проверку цены прошел , proxy : {proxy}')
    
            if 'error_code' in price_info:
                print(f"Ошибка получения цена - {price_info['message']}")
                return

            message_text = f'<b>{price_info["data"]["name"]}</b>\n{message_text}\n'

            percent = price_info["data"]["diffInPercents"]
            average_price = price_info["data"]["averagePrice"]
            current_price = price_info["data"]["currentPrice"]

            t = message_text.split('\n')[0]
            
            if percent <= 0 and abs(percent) >= user_percent:
                # and int(re.sub('\D', '',t)[-4:]) >= user_date
                res = average_price - current_price
                message_text += f"<b> Дешевле на {res} T или на {str(abs(percent))} % </b>"
                print(f'<b> Дешевле на {res} T или на {str(abs(percent))} % </b>')

                try:
                    # print(message_text)
                    await send_to_tg(message_text)
                    await send_to_tg_2(message_text)
                    print(f'MESSAGE SEND TO TG ')
                except:
                    print(f'!!! ERROR MESSAGE SENT to  ')
            else:
                print('Не прошли по цене.')
import time
async def main():
    city = input("Введите город (на русском): ")
    percent = float(input("На сколько процентов машина должна быть дешевле: "))
    user_date = int(input('Укажите минимальный год машины: '))
    
    start_time = time.time()
    with open('proxies100.txt', 'r') as file:
        proxies = file.read().splitlines()

    search_city = await search_cities_category(city,random.choice(proxies))
    if search_city is not None:
        print(f'Город найден : {search_city}')
        cnt = 1
        while True:
            now = datetime.now()
            data = now.strftime('%d.%m.%y %I:%M:%S')
            print(f"{cnt} - {data} - parsing")
            try:
                await run_parse(search_city, percent,user_date,proxies)
            except Exception as e:
                print(e)
                await asyncio.sleep(random.uniform(1, 20))

            await asyncio.sleep(random.uniform(1, 20))
            cnt+=1
        
            end_time = time.time()
            iteration_time = end_time - start_time
            print(f"Время потраченое для : {cnt}: {iteration_time} seconds")
            start_time = time.time()
    else:
        print('Город не найден. Завершение программы.')

asyncio.run(main())
