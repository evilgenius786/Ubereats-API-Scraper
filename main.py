import csv
import os
import re
from datetime import datetime
from urllib.parse import quote_plus

import openpyxl
import requests
from bs4 import BeautifulSoup

import json

test = True
fieldnames = ["site_url", "script_start_time", "category", "subcategory", "item_image_url", "item_description",
              "item_price", "delivery_fee"]
encoding = 'utf8'


def getApi(filename: str, store: str, sections: list):
    print(f"Got StoreID: {store} Sections: {sections}")
    location = {"address": {
        "address1": "Colombo",
        "address2": "",
        "aptOrSuite": "",
        "eaterFormattedAddress": "Colombo, Sri Lanka",
        "subtitle": "",
        "title": "Colombo",
        "uuid": ""
    },
        "latitude": 6.9270786,
        "longitude": 79.861243,
        "reference": "ChIJA3B6D9FT4joRjYPTMk0uCzI",
        "referenceType": "google_places",
        "type": "google_places",
        "source": "manual_auto_complete",
        "addressComponents": {
            "countryCode": "",
            "firstLevelSubdivisionCode": "",
            "city": "",
            "postalCode": ""
        },
        "originType": "user_autocomplete"
    }
    headers = {
        'content-type': 'application/json',
        'cookie': f'uev2.loc={quote_plus(json.dumps(location)).replace("+", "")};',
        'x-csrf-token': 'x'
    }
    payload = json.dumps({
        "diningMode": "DELIVERY",
        "sectionUUIDs": sections,
        "storeUUIDs": [store]
    })
    url = "https://www.ubereats.com/api/getCatalogItemsBySectionV1"
    response = requests.post(url, data=payload, headers=headers)
    # print(response.text)
    with open(f"./json/{filename}", 'w') as outfile:
        json.dump(response.json(), outfile, indent=4)
    # print("Save to file: " + filename)
    return response.json()


def main():
    logo()
    if not os.path.isdir('json'):
        os.mkdir('json')
    if not os.path.isdir('ProcessedJson'):
        os.mkdir('ProcessedJson')
    if not os.path.isfile('UberEats.csv'):
        with open("UberEats.csv", 'w', encoding=encoding, newline='') as outfile:
            csv.DictWriter(outfile, fieldnames=fieldnames).writeheader()
    with open('urls.txt', 'r') as f:
        urls = f.read().splitlines()
    for url in urls:
        filename = url.split('/store/')[1].replace('/', '_').split("?")[0] + '.json'
        scraped = os.listdir('./json')
        if filename not in scraped:
            getProducts(url, filename)
        else:
            print(f"Already scraped {url}")


def getProducts(store_url: str, filename: str):
    print(f"Fetching categories and subcategories for {store_url}")
    soup = getSoup(store_url)
    js = soup.find('script', {'id': '__REDUX_STATE__'}).text
    names = [x for x in re.findall(r'{\\u0022title\\u0022:{\\u0022text\\u0022:\\u0022(.*?)\\u0022', js)]
    sections = [x.replace("\\u0022", "")[1:-1] for x in re.findall('catalogSectionUUID(.*?)payload', js)]
    d = {s: n for s, n in zip(sections, names)}
    # print(json.dumps(d, indent=4))
    store = re.findall('menuUUID(.*?)menuDisplayType', js)[0].replace("\\u0022", "")[1:-1]
    js = getApi(filename, store, sections)
    processJson(store_url, js, d, soup, filename)


def processJson(url: str, js: dict, d: dict, soup: BeautifulSoup, filename: str):
    data = {}
    products = []
    # iterating through each category in JSON
    for cat in js['data'].keys():
        c = d[cat] if cat in d else cat
        # print(f"Working on category {cat} {c}")
        data[c] = {
            "URL": url,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "DeliveryFee": soup.find('div', string="Delivery").find_parent('div').text.strip(),
        }
        # iterating through each subcategory in JSON
        for subcat in js['data'][cat]:
            # the data required is in the "payload" key so navigating to that,
            # check the JSON structure in the "json" directory for details
            payload = subcat['payload']['standardItemsPayload']
            title = payload['title']['text'].strip()
            if title in ["Picked for you", "Save on Select Items"]:
                continue
            data[c][title] = []
            for item in payload['catalogItems']:
                product = {
                    "site_url": url,
                    "script_start_time": data[c]["Time"],
                    "category": c,
                    "subcategory": title,
                    "item_image_url": item['imageUrl'],
                    "item_description": item['title'],
                    "item_price": round(item['price'] / 100, 2),
                    "delivery_fee": soup.find('div', string="Delivery").find_parent('div').text.strip(),
                }
                products.append(product)
                data[c][title].append({
                    "Name": item['title'],
                    "Price": round(item['price'] / 100, 2),
                    "Image": item['imageUrl'],
                })
    # print(json.dumps(data, indent=4))
    with open('ProcessedJson/' + filename, 'w') as outfile:
        json.dump(data, outfile, indent=4)
    with open("UberEats.csv", 'a', encoding=encoding, newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writerows(products)
    convert("UberEats.csv")


def convert(filename: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    with open(filename, encoding=encoding) as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            ws.append(row)
    wb.save(filename.replace(".csv", ".xlsx"))


def logo():
    os.system('color 0a')
    print(r"""
                          (                                 (     
               (          )\ )             (        *   )   )\ )  
        (    ( )\   (    (()/(     (       )\     ` )  /(  (()/(  
        )\   )((_)  )\    /(_))    )\   ((((_)(    ( )(_))  /(_)) 
     _ ((_) ((_)_  ((_)  (_))     ((_)   )\ _ )\  (_(_())  (_))   
    | | | |  | _ ) | __| | _ \    | __|  (_)_\(_) |_   _|  / __|  
    | |_| |  | _ \ | _|  |   /    | _|    / _ \     | |    \__ \  
     \___/   |___/ |___| |_|_\    |___|  /_/ \_\    |_|    |___/  
=======================================================================
        UberEats stores data scraper by github.com/evilgenius786
=======================================================================
[+] API Based
[+] Duplicate check
[+] JSON output
[+] Multithreaded
_______________________________________________________________________
""")


def getSoup(url):
    # if test:
    #     return BeautifulSoup(open('test.html'), 'html.parser')
    return BeautifulSoup(requests.get(url).text, 'lxml')



if __name__ == '__main__':
    main()
    # getProducts(
    #     'https://www.ubereats.com/store/dropofflk-borella/4FkArcAXSrmojRTH84kgIA?diningMode=DELIVERY&pl=JTdCJTIyYWRkcmVzcyUyMiUzQSUyMkNvbG9tYm8lMjIlMkMlMjJyZWZlcmVuY2UlMjIlM0ElMjJDaElKQTNCNkQ5RlQ0am9SallQVE1rMHVDekklMjIlMkMlMjJyZWZlcmVuY2VUeXBlJTIyJTNBJTIyZ29vZ2xlX3BsYWNlcyUyMiUyQyUyMmxhdGl0dWRlJTIyJTNBNi45MjcwNzg2JTJDJTIybG9uZ2l0dWRlJTIyJTNBNzkuODYxMjQzJTdE')
