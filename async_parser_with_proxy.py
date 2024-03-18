import asyncio
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from bs4 import BeautifulSoup
import re
import random
import time
import requests

url_list = [""]

async def send_to_tg(text):
    send_text = 'https://api.telegram.org/bot' + 'TOKEN' + \
        '/sendMessage?chat_id=' + "CHAT_ID" + '&parse_mode=HTML&text=' + text
    async with ClientSession() as session:
        async with session.get(send_text) as response:
            return await response.text()

def search_cities_category(search_city):
    url = 'https://m.kolesa.kz/regions/all/?categoryName=auto.car'
    response = requests.get(url)
    if response.status_code == 200:
        for city in response.json():
            if str(city['value']).lower() == search_city.lower():
                print(city['alias'])
                return city['alias'] # work 
    else:
        print(f'NO DATA FOR THIS CITY:{search_city}')
        return
           


async def fetch(url, proxy_url):
    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        async with session.get(url, proxy=proxy_url) as response:
            return await response.text()

async def load_proxies(file_path):
    proxy_list = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(':')
            proxy_url = f"http://{parts[0]}:{parts[1]}@{parts[2]}:{parts[3]}"
            proxy_list.append(proxy_url)
    return proxy_list

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
async def run_parse(search_city,user_percent,user_date, proxy_url):
    headers = {'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0'}
    async with ClientSession(headers=headers) as session:
        url = f"https://m.kolesa.kz/cars/{search_city}"
        params = {'auto-custom':2}
        
        await asyncio.sleep(random.uniform(1, 3))
        html = await fetch(url, proxy_url)
        
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
        
        cars_ids.append(card_id)  # Добавляем ID машины в список проверенных
        print(f'Проверяем машину с ID {card_id}')

        if(a is None) or (url_list[0] == href):
            return

        url_list[0] = href
        pattern = "https://m.kolesa.kz"
        card_url = f'{pattern}{href}'
        message_text = f'{card_url}"\n"'

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
        card_text = await fetch(card_url, proxy_url)
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

        async with session.get(price_info_url) as response:
            price_info = await response.json()

async def main():
    city = input("Введите город (на русском): ")
    percent = float(input("На сколько процентов машина должна быть дешевле: "))
    user_date = int(input('Укажите минимальный год машины: '))

    proxy_list = await load_proxies("100proxies.txt")  # Загружаем список прокси из файла

    start_time = time.time()

    search_city = search_cities_category(city)
    if search_city is not None:
        print(f'Город найден : {search_city}')
        cnt = 1
        while True:
            now = datetime.now()
            data = now.strftime('%d.%m.%y %I:%M')
            print(f"{cnt} - {data} - parsing")
            try:
                proxy_url = random.choice(proxy_list)  # Выбираем случайный прокси из списка
                await run_parse(search_city, percent, user_date, proxy_url)
            except Exception as e:
                print(e)
                await asyncio.sleep(random.uniform(1, 20))

            await asyncio.sleep(random.uniform(1, 20))
            cnt+=1
        
            end_time = time.time()
            iteration_time = end_time - start_time
            print(f"Время потраченное на итерацию {cnt}: {iteration_time} seconds")
            start_time = time.time()
    else:
        print('Город не найден. Завершение программы.')

if __name__ == "__main__":
    asyncio.run(main())
