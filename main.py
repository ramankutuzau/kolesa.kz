
from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup
import requests
import re
# import sets
from fake_useragent import UserAgent

pattern = "https://m.kolesa.kz"
list = [""]


# def send_to_tg(text,chat_id):
#     send_text = 'https://api.telegram.org/bot' + sets.bot_token + \
#         '/sendMessage?chat_id=' + chat_id + '&parse_mode=HTML&text=' + text
#     requests.get(send_text)

def send_to_tg(text):
    send_text = 'https://api.telegram.org/bot' + '6940107238:AAH0oYf1a8p4MpzyeEJq1vQA6vdcV6AyE7Q' + \
        '/sendMessage?chat_id=' + "717945869" + '&parse_mode=HTML&text=' + text
    requests.get(send_text)

def get_all_cities():
    url = 'https://m.kolesa.kz/regions/all/?categoryName=auto.car'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []


def test(searchCity,user_percent):
    alias = ''
    headers = {'User-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0'}
    params = {'auto-custom':2}
    
    session = requests.Session()
    city_list = get_all_cities()

    

    if not city_list:
        print(f'NO DATA FOR THIS CITY:{searchCity}')
        return
    for city in city_list:
        if str(city['value']).lower() == searchCity.lower():
            alias = city['alias'] # work 
            break
            # work
   
    url = f"https://m.kolesa.kz/cars/{alias}"

    ua = UserAgent()
    headers['User-Agent'] = ua.random
    session.headers.update(headers)
    
    response = session.get(url, params=params)
    text = response.text
    
    # text = session.get(url,headers=headers,params=params).text
    
    
    sleep(5)
    
    bs = BeautifulSoup(text, "html.parser")

    cars = bs.find_all(class_="search-list__item")
    
    last_car = cars[0]
   


    a = last_car.find("a")
    href = a['href']
    card_id = href.split('/')[-1]
    if(a is None) or (list[0] == href): return

    list[0] = href
    card_url = f'{pattern}{href}'
    message_text = f'{card_url}"\n"'

    print(message_text)
    
    card_text = session.get(card_url,headers=headers).text
    sleep(30) # 60


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
    
   
    price_info = requests.get(f"https://m.kolesa.kz/a/average-price/{card_id}").json()
    print(f'Получение цены авто : {price_info["data"]["name"]}')
    sleep(15) # 60
    print(f'Разница в процентах : {abs(price_info['data']['diffInPercents'])} | Средняя цена: {price_info['data']['averagePrice']} | Текущая цена: {price_info['data']['currentPrice']}')
    if 'error_code' in price_info:
        print(f"ОШИБКА ПРАЙС ИНФО - {price_info['message']}")
        return

    message_text = f'<b>{price_info["data"]["name"]}</b>\n{message_text}\n'

    percent = price_info["data"]["diffInPercents"]
    average_price = price_info["data"]["averagePrice"]
    current_price = price_info["data"]["currentPrice"]

    t = message_text.split('\n')[0]
    # print(t)
    if percent <= 0 and abs(percent) >= user_percent and int(re.sub('\D', '',t)[-4:]) >= user_date:
        res = average_price - current_price
        message_text += f"<b> Дешевле на {res} T или на {str(abs(percent))} % </b>"
        print(message_text)

        try:
            print(message_text)
            send_to_tg(message_text)
            # send_to_tg(message_text,chat_id)
            print(f'MESSAGE SENT to')
        except:
            print(f'!!! ERROR MESSAGE SENT to  ')




if __name__ == "__main__":
    city = input("Введите город (на русском): ")
    percent = float(input("На сколько процентов машина должна быть дешевле: "))
    user_date = int(input('Укажите минимальный год машины: '))

    cnt = 1

    while True:
        now = datetime.now()
        data = now.strftime('%d.%m.%y %I:%M')
        print(f"{cnt} - {data} - parsing")
        try:
            test(city, percent)
        except Exception as e:
            print(e)
            sleep(30)

        sleep(10)
        cnt+=1

