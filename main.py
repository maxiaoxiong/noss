import json
import math
import random
import sys

import requests
import string
import threading
import time
import websocket
import logging
import multiprocessing

from pynostr.event import Event
from pynostr.key import PrivateKey
from pow import PowEvent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
event_id_path = "event_id.txt"
block_height_path = "block_height.txt"
seq_witness_path = "seq_witness.txt"


# 获取最新事件id
def open_ws():
    def on_open(ws):
        logging.info("连接中继服务器中...")

    def on_message(ws, msg):
        # 更新全局的event id到文件
        event_id = json.loads(msg)["eventId"]
        logging.info(f"更新event_id {event_id}")
        with open(event_id_path, "w") as file:
            file.write(event_id)

    def on_close(ws):
        logging.info("与中继服务器断开连接")

    def on_error(ws, error):
        logging.error("中继服务器报错: {}".format(error))

    ws = websocket.WebSocketApp("wss://report-worker-2.noscription.org/",
                                on_open=on_open,
                                on_message=on_message,
                                on_close=on_close,
                                on_error=on_error,
                                header={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
                                    'Sec-WebSocket-Version': '13',
                                    'Accept-Encoding': 'gzip, deflate, br',
                                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                                    'Sec-WebSocket-Key': 'lzAOYPq7IZeg+yB9zfHSfw=='})
    ws.run_forever()


def get_block_from_rpc():
    url_list = [
        "https://arbitrum-one.publicnode.com"
        "https://arb-mainnet.unifra.io/v1/bb7f9fd643754558bf204157b1af7931",
        "https://arbitrum.blockpi.network/v1/rpc/829a98f75d90ce7116e40fba9655b4d7dcb770db",
        "https://arbitrum-mainnet.infura.io/v3/80c0d6915cac453cb8e5b1facfaecc21",
        "https://go.getblock.io/cf5a563f7de0420c90f6a81d357ed7a2",
        "https://arb-mainnet.g.alchemy.com/v2/9KyAxglA5DqtMsGyDJ0gZvPot9o9skmJ",
        "https://arbitrum.llamarpc.com",
        "https://endpoints.omniatech.io/v1/arbitrum/one/public",
        "https://endpoints.omniatech.io/v1/arbitrum/one/public",
        "https://rpc.arb1.arbitrum.gateway.fm",
        "https://lb.nodies.app/v1/3a59dad98dc84331ad26e7152934643a",
        "https://rpc.ankr.com/arbitrum",
        "https://arbitrum.blockpi.network/v1/rpc/public",
        "https://arb1.arbitrum.io/rpc",
        "https://1rpc.io/arb",
        "https://arb-pokt.nodies.app",
        "https://arbitrum-one.public.blastapi.io",
        "https://arb-mainnet-public.unifra.io",
        "https://arbitrum.api.onfinality.io/public",
        "https://arbitrum.meowrpc.com",
        "https://arbitrum.drpc.org"
    ]

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "content-type": "application/json",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Microsoft Edge\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site"
    }
    genius_block = 165968698
    current_block = math.ceil(genius_block + (time.time() - 1704112210) * 4)
    current_block_height = str(hex(current_block))
    body = {
        "method": "eth_getBlockByNumber",
        "params": [current_block_height, False],
        "id": 1,
        "jsonrpc": "2.0"
    }
    while True:
        for url in url_list:
            try:
                response = requests.post(url, headers=headers, json=body)
                data = response.json()
                if "result" in data and data['result'] is not None:
                    # 更新 current_block_height 和 seqWitness
                    seq_witness = data["result"]["hash"]
                    logging.info(
                        f"更新全局区块高度 {current_block}, 16进制表示为 {current_block_height}, 关联地址为 {seq_witness}")
                    with open(block_height_path, "w") as file:
                        file.write(str(current_block))
                    with open(seq_witness_path, "w") as file:
                        file.write(seq_witness)
                    time.sleep(1)
                else:
                    logging.error(f"获取区块高度失败 {url}, {body}, {data}")
            except Exception as e:
                logging.error(f"请求区块高度失败 {url}, {e}")


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
    logging.info(f"挖掘成功 {e}, 提交结果 {response.text}")


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


def mine_data_and_submit(identity_pk):
    def nonce():
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=13))

    def now():
        return int(time.time())

    pub_key = identity_pk.public_key.hex()
    # 设置挖矿难度
    pe = PowEvent(difficulty=21)
    while True:
        e_copy = Event(
            content=json.dumps({"p":"nrc-20","op":"mint","tick":"noss","amt":"10"}),
            kind=1,
            pubkey=pub_key,
            tags=[
                ["p", "9be107b0d7218c67b4954ee3e6bd9e4dba06ef937a93f684e42f730a0c3d053c"],
                ["e", "51ed7939a984edee863bfbb2e66fdc80436b000a8ddca442d83e6a2bf1636a95",
                 "wss://relay.noscription.org/", "root"],
            ]
        )
        event_id, block_height, pre_addr = get_var(1), get_var(2), get_var(3)
        e_copy.created_at = now()
        e_copy.tags.append(["e", event_id, "wss://relay.noscription.org/", "reply"])
        e_copy.tags.append(["seq_witness", block_height, pre_addr])
        e_copy.tags.append(["nonce", nonce(), "21"])
        while True:
            # 这里稍微修改了一下源码，有点蛋疼
            e_copy = pe.mine(e_copy)
            if pe.calc_difficulty(e_copy) >= 21:
                break
        # 还原被覆盖的参数 block_height
        e_copy.created_at = now()
        sk = PrivateKey(bytes.fromhex(identity_pk.hex()))
        sig = sk.sign(bytes.fromhex(e_copy.id))
        e_copy.sig = sig.hex()
        post_event(e_copy.to_dict())
        logging.info(f"{threading.current_thread()} 挖掘中...")


def check_env():
    logging.info("检查环境中...")
    while True:
        event_id = get_var(1)
        if event_id is None or event_id == '':
            logging.warning(f"event_id 不存在, 5秒后重新检查")
            time.sleep(5)
            continue
        block_height = get_var(2)
        if block_height is None or block_height == '':
            logging.warning(f"block_height 不存在, 5秒后重新检查")
            time.sleep(5)
            continue
        seq_witness = get_var(3)
        if seq_witness is None or seq_witness == '':
            logging.warning(f"seq_witness 不存在, 5秒后重新检查")
            time.sleep(5)
            continue
        break
    logging.info("环境检查完成，开始运行!!!")


if __name__ == "__main__":
    thread_num = 30
    if len(sys.argv) < 1:
        logging.info(f'线程数量设置为: {sys.argv[1]}')
        thread_num = int(sys.argv[1])
    process_list = []
    # 初始化钱包
    identity_pk = PrivateKey.from_nsec("@@")
    pub_key = identity_pk.public_key.hex()
    logging.info(f"pub key: {pub_key}")
    # 开启进程获取event_id的线程
    p1 = multiprocessing.Process(target=open_ws)
    # 开启获取最新区块高度的线程
    p2 = multiprocessing.Process(target=get_block_from_rpc)
    p1.start()
    process_list.append(p1)
    p2.start()
    process_list.append(p2)
    # 检查环境
    check_env()
    try:
        for i in range(thread_num):
            process = multiprocessing.Process(target=mine_data_and_submit,
                                              args=(identity_pk,))
            process.start()
            logging.info(f"启动进程 {process.pid} 并开始挖矿")
            process_list.append(process)
    except KeyboardInterrupt:
        for process in process_list:
            process.terminate()
            process.join()
        print("所有进程执行完毕")
