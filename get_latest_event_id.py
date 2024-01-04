from loguru import logger
import websocket
import json


class GetLatestEventId:

    def __init__(self):
        self.event_id = ""

    def on_open(self, ws):
        logger.info("connecting get event id server...")

    def on_message(self, ws, msg):
        try:
            event_id = json.loads(msg)["eventId"]
            if self.event_id != event_id:
                self.event_id = event_id
                logger.debug(f"update latest_event_id: {self.event_id}")
        except Exception as e:
            logger.error(f"get latest event id error {e}")

    def on_close(self, ws):
        logger.info("closed get event id server")

    def on_error(self, ws, error):
        logger.error("get event id error: {}".format(error))

    def run(self):
        ws = websocket.WebSocketApp("wss://report-worker-2.noscription.org/",
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_close=self.on_close,
                                    on_error=self.on_error,
                                    header={
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
                                        'Sec-WebSocket-Version': '13',
                                        'Accept-Encoding': 'gzip, deflate, br',
                                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                                        'Sec-WebSocket-Key': 'lzAOYPq7IZeg+yB9zfHSfw=='})
        ws.run_forever(reconnect=True)
