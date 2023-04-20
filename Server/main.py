import openai
import requests
from bs4 import BeautifulSoup
from socket import *  # For Server Socket
from PIL import Image
from io import BytesIO
import os
import time
import urllib.request

global api_key
global weather
global query

api_key = 'Your Open AI API'

def getweather():
    global temperature, weather
    html = requests.get('http://search.naver.com/search.naver?query=수내+날씨')
    soup = BeautifulSoup(html.text, 'html.parser')

    # Weather Information
    weather_data = soup.find('div', {'class': 'weather_info'})

    # Current Temperature
    temperature = (str(weather_data.find('div', {'class': 'temperature_text'}).text.strip()[5:])[:-1])

    # Weather Status
    weatherStatus = weather_data.find('span', {'class': 'weather before_slash'}).text

    if weatherStatus == '맑음':
        weather = 'Sunny'
    elif '흐림':
        weather = 'Cloud'

    print(temperature)
    print(weather)

def Chat_GPT(api_key, query):
    global answer

    openai.api_key = api_key

    model = "gpt-3.5-turbo"

    messages = [
        {
            "role": "system",
            "content": "You are a very creative and interesting writer."
        },
        {
            "role": "user",
            "content": query
        }
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )
    answer = response['choices'][0]['message']['content']
    print(answer)

def dall_e2(answer):
    global image_url
    global image_data
    response = openai.Image.create(
        prompt=answer,
        n=1,
        size="256x256",
    )
    image_url = response['data'][0]['url']
    urllib.request.urlretrieve(image_url, "test.bmp")

    im = Image.open("test.bmp")
    im_resized = im.resize((220, 220))

    im_resized = im_resized.convert('P', palette=Image.ADAPTIVE, colors=16)

    im_resized.save("test_resized.bmp", format="BMP")
    with open("test_resized.bmp", "rb") as f:
        image_data = f.read()
    print(image_data)

# Server Socket Make
serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('', 5000))
serverSock.listen(1)
print("Ready ")
connectionSock, addr = serverSock.accept()

print(str(addr), 'Connected Client')

while True:
    getweather()
    query = "The current weather is very {} with {} degrees. Create a creative story in this situation. No more than two sentences.".format(weather,temperature)
    print(query)

    Chat_GPT(api_key,query)
    answer = "Picasso's painting of the story. '{}'".format(answer)
    print(answer)
    dall_e2(answer)
    len_sent = f"LEN:{len(image_data)}".encode()
    print(f"length of sent data = {len_sent}")
    connectionSock.send(len_sent)
    time.sleep(1)
    connectionSock.send(image_data)

    print(image_url)

    time.sleep(30)
#    break
