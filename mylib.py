from time import time, sleep
import random
import os

dirname = os.path.dirname(__file__)

def get_proxy(pm):
    max_list = 0
    if pm != True:
        with open(f'{dirname}/data_files/proxy.txt', 'r') as file:
            proxy_list = file.read().splitlines()
            max_list = len(proxy_list)
            item = random.randint(0, max_list)
            result = proxy_list[item]
            result = {"http": "http://" + result, "https": "http://" + result}
            # print(result)
    else:
        result = {"http": None, "https": None}
    return result

def get_ua():
    max_list = 0

    with open(f'{dirname}/data_files/useragents.txt', 'r') as file:
        user_agents = file.read().splitlines()
        max_list = len(user_agents)
        item = random.randint(0, max_list-1)
        result = user_agents[item]
        # print(result)
    return result


def error_logging(data, filename):
    with open("logs/" + filename, 'a+', encoding='utf-8') as file:
       file.write(data + '\n')

def req_delay(secs_from, secs_to):
    secs = random.randint(secs_from, secs_to)
    print(f'Delay {secs} seconds...')
    sleep(secs)