import json
import logging
import random
import string
import sys
import threading
import time
from loguru import logger

import requests
from get_latest_event_id import GetLatestEventId
from pynostr.key import PrivateKey
from web3 import Web3
from multiprocessing import Pool, Manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
event_id_path = "event_id.txt"
block_height_path = "block_height.txt"
seq_witness_path = "seq_witness.txt"


def get_latest_block():
    web3 = Web3(Web3.HTTPProvider("https://arbitrum-one.publicnode.com"))
    while True:
        if web3.is_connected():
            latest_block_number = web3.eth.block_number
            latest_block_hash = web3.eth.get_block(latest_block_number)['hash'].hex()
            with open(block_height_path, "w") as file:
                file.write(str(latest_block_number))
            with open(seq_witness_path, "w") as file:
                file.write(latest_block_hash)
            logging.info(f"The latest block number is: {latest_block_number}, {latest_block_hash}")
            return str(latest_block_number), latest_block_hash
        else:
            logging.error("cannot connect to Arbitrum network, retrying...")


def post_event(e):
    url = "https://api-worker.noscription.org/inscribe/postEvent"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "content-type": "application/json",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }

    response = requests.post(url, headers=headers, json=e)
    logging.info(f"success {response.text}, tx {e}")


def get_var(v):
    global event_id_path, block_height_path, seq_witness_path
    path = None
    if v == 1:
        path = event_id_path
    elif v == 2:
        path = block_height_path
    elif v == 3:
        path = seq_witness_path
    try:
        with open(path, "r") as file:
            val = file.read().strip()
            return val
    except IOError:
        print(f"读取文件 '{path}' 时发生错误")
        return None


def check_env():
    logging.info("Checking env..")
    while True:
        event_id = get_var(1)
        if event_id is None or event_id == '':
            logging.warning(f"event_id not exist, retry after 5s")
            time.sleep(5)
            continue
        block_height = get_var(2)
        if block_height is None or block_height == '':
            logging.warning(f"block_height not exist, retry after 5s")
            time.sleep(5)
            continue
        seq_witness = get_var(3)
        if seq_witness is None or seq_witness == '':
            logging.warning(f"seq_witness not exist, retry after 5s")
            time.sleep(5)
            continue
        break
    logging.info("env checked，Running!!!")


def get_latest_event_id(share_dict):
    print(share_dict)
    event_instance = GetLatestEventId()
    event_instance.run()
    while True:
        print(share_dict, event_instance.event_id)
        if share_dict['event_id'] == event_instance.event_id:
            time.sleep(0.1)
            continue
        else:
            share_dict['event_id'] = event_instance.event_id
            logger.success(f"update global event id {share_dict['event_id']}")


if __name__ == "__main__":
    thread_cnt = 1
    manager = Manager()
    share_dict = manager.dict()

    pool = Pool(processes=2)
    pool.apply_async(get_latest_event_id, args=(share_dict,))

    pool.close()
    pool.join()
