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

api_key = 'Your API Key'

def Chat_GPT(api_key, query):
    global answer

    openai.api_key = api_key

    model = "gpt-3.5-turbo"

    messages = [
        {
            "role": "system",
            "content": "You are the best tarotist."
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
    with open("back1234.bmp", "rb") as f:
        image_data = f.read()
    print(image_data)

    len_sent = f"LEN:{len(image_data)}".encode()
    print(f"length of sent data = {len_sent}")
    connectionSock.send(len_sent)
    time.sleep(1)
    connectionSock.send(image_data)
    time.sleep(1)

    while True:
        data = connectionSock.recv(2)
        if not data:
            continue
        data = data.decode()
        card_num: str = ''
        print(f"received={data}")
        if data == '1':
            card_num = 'first'
        elif data == '2':
            card_num = 'second'
        elif data == '4':
            card_num = 'third'
        elif data == '8':
            card_num = 'fourth'

        query = "4 random cards flipped on pamela colman smith rws tarot deck." \
                "I picked the {} card. Please explain what this card is like. Please explain within 3 sentences".format(card_num)
        print(query)
        Chat_GPT(api_key, query)
        dall_e2(answer + "High quality")
        len_sent = f"LEN:{len(image_data)}".encode()
        print(f"length of sent data = {len_sent}")
        connectionSock.send(len_sent)
        time.sleep(1)
        connectionSock.send(image_data)
        time.sleep(1)
        break

    done = False
    sent = False
    while True:
        data = connectionSock.recv(100)
        if not data:
            continue
        print(f"received={data}")
        # if client sent OK all is done
        if data == b"OK":
            done = True
        if not sent:
            ret = connectionSock.send(answer.encode())
            sent = True
        # quit when client received my response
        if done:
            connectionSock.close()
            break
    # wait reset

    while True:
        data = connectionSock.recv(100)
        if not data:
            continue
        print(f"received={data}")
        # if client sent OK all is done
        if data == b"Reset":
            done = True
        break
    break