from bs4 import BeautifulSoup
import requests
from threading import Thread
import json
from datetime import datetime
import os
import re
import mylib
from multiprocessing import Pool


dirname = os.path.dirname(__file__)
proxyless_mode = False





with open(dirname + "\\data_files\\full_items_list.txt", 'r', encoding='utf-8') as file:
    items_list = file.read().splitlines()


def get_main_data():
    item = items_list.pop(-1)
    print(f'Remaining {len(items_list)} items')
    item_part = item.split(';', 5)
    item_url = item_part[2]
    item_name = item_part[0]
    item_id = item_part[1]

    i_count = 1
    user_agent = mylib.get_ua()
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "clientId": "mHPVWnzuBkrW7rmt56XGwKkb5Gp9BJMk",
    }

    def process_get_req():
                # GET JSON
        proxy = mylib.get_proxy(proxyless_mode)
        #print('Using proxy' + str(proxy))
        req = requests.get(item_url, headers=headers, proxies=proxy)
        src = req.text
        json_part = re.search('(?<=\ id="__NEXT_DATA__"\ type="application/json">).*?(?=</script>)', src)
        json_part = json_part.group(0)
        # with open(dirname + "\\data_files\\few_jsons.txt", 'a+', encoding='utf-8') as file:
        #     file.write(json_part + '\n')
                # GET TOKEN
        req_head = req.headers
        token_reg = re.search('"token":"(.+?)","expires"', str(req_head))
        token = token_reg.group(1)
        return token, json_part, req.status_code, proxy

    data_parts = []

    try:
        data_parts = process_get_req()
    except:
        items_list.append(item)
        i_count = i_count + 1
        print(f'Retry: {i_count}')
        data_parts = process_get_req()


    token = data_parts[0]
    json_part = data_parts[1]
    status_code = data_parts[2]
    proxy = data_parts[3]



    json_part = json.loads(json_part)


            # GET MAIN VALUES

    def get_dimensions():

        full_dimensions = json_part['props']['pageProps']['initialState']['productDetails']['productdata']['dimension']['packages'][0]
        temp_list = []
        for key, value in full_dimensions.items():
            temp_list.append(f'{key}: {value}')
        str_dimm = '\n'.join(temp_list)


        return str_dimm

    def get_category():
        full_categoris = json_part['props']['pageProps']['initialState']['productDetails']['productdata']['allCategories']
        #print(full_categoris)
        temp_list = []
        for cat in full_categoris:
            temp_list.append(cat['displayName'])
        return temp_list[-1]

    def get_specs():
        full_specs = json_part['props']['pageProps']['initialState']['productDetails']['productdata']['classifications'][0]['features']
        #print(full_specs)
        temp_dict = {}
        specs = []
        for part in full_specs:
            temp_dict[part['name']] = part['featureValues'][0]['value']
        #print(temp_dict)
        try:
            model = temp_dict['Model Number']
            temp_dict.pop('Model Number')
        except:
            model = None
        try:
            Colour = temp_dict['Colour']
            temp_dict.pop('Colour')
        except:
            Colour = None


        #print(temp_dict)
        for key, value in temp_dict.items():
            specs.append(f'{key}: {value}')
        specs_str = '\n'.join(specs)
        return model, specs_str, Colour

    def get_features():
        full_feat = json_part['props']['pageProps']['initialState']['productDetails']['productdata']['feature']['pointers']
        str_feat = '\n'.join(full_feat)
        return str_feat

    def get_images():
        img_part = json_part['props']['pageProps']['initialState']['productDetails']['productdata']['images']
        img_temp_list = []
        for img in img_part:
            img_temp_list.append(img['url'])
        return img_temp_list



    specs_parts = get_specs()
    model = specs_parts[0]
    specificagion = specs_parts[1]
    Colour = specs_parts[2]
    brand = json_part['props']['pageProps']['initialState']['productDetails']['productdata']['brand']['name']
    description = json_part['props']['pageProps']['initialState']['productDetails']['productdata']['feature']['description']
    dimensions = get_dimensions()
    category = get_category()
    features = get_features()
    images_list = get_images()


    # GET PRICE
    i_price = 0

    def get_price(proxy):
        #print('Using proxy' + str(proxy))
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "clientId": "mHPVWnzuBkrW7rmt56XGwKkb5Gp9BJMk",
            "country": "AU",
            "currency": "AUD",
            "locale": "en_AU",
            "userId": "anonymous",
            "locationCode": "6400",
            "X-region": "VICMetro",
            "Authorization": "Bearer " + token
        }
        price_req = requests.get(f'https://api.prod.bunnings.com.au/v1/products/{item_id}/fulfillment/6400/radius/100000?isToggled=true', headers=headers, proxies=proxy)
        price_src = price_req.text
        price_js = json.loads(price_src)

        price = price_js['data']['price']['value']
        #print(price)
        return price
    price = None
    price = get_price(proxy)


    # PREPARE JSON

    images_list = get_images()

    main_json = {}
    main_json['gtin'] = None
    main_json['unique_id'] = item_id
    main_json['name'] = item_name
    main_json['source_url'] = item_url
    main_json['specification'] = specificagion
    main_json['Colour'] = Colour
    main_json['brand'] = brand
    main_json['price'] = price
    main_json['description'] = description
    main_json['dimensions'] = dimensions
    main_json['product_category'] = category
    main_json['features'] = features
    main_json['product_model'] = model

    i = 0
    for img in images_list:
        main_json[f'image_{str(i)}'] = img
        i = i+1
    #print(main_json)
    final_json = json.dumps(main_json, ensure_ascii=False)


    with open(dirname + "\\data_files\\json_output.json", 'a+', encoding='utf-8') as file:
        file.write(final_json + ',\n')


def main_data_multithread():
    threads_list = []  # Threads Array

    def threads_init(name_func, args):
        for x in range(args):
            threads_list.append(Thread(target=name_func))
            print(threads_list)

    threads_init(get_main_data, main_data_threads)

    for thr in threads_list:
        thr.start()
    #print('starting threads')
    for thr in threads_list:
        thr.join()


# RUN MULTITHREAD
main_data_threads = 30
main_data_processes = 4

while len(items_list) > 0:
    main_data_multithread()