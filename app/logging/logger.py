from loguru import logger
import sys
import requests
import json

class LokiHandler:
    def __init__(self, loki_url):
        self.loki_url = loki_url

    def write(self, message):
        log_entry = {
            "streams": [
                {
                    "labels": '{app="vampire"}',
                    "entries": [{"line": message.rstrip()}]
                }
            ]
        }
        try:
            requests.post(
                self.loki_url,
                data=json.dumps(log_entry),
                headers={"Content-Type": "application/json"},
                timeout=0.5
            )
        except Exception as e:
            print(f"[LokiHandler] Failed to send log: {e}")

    def flush(self):
        pass


logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add(LokiHandler("http://loki:3100/loki/api/v1/push"), level="INFO")

 
# TODO: интеграция с Grafana/Loki/Elasticsearch 