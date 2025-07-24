from loguru import logger
import sys

# import requests
# import json
#
# class LokiHandler:
#     def __init__(self, loki_url):
#         self.loki_url = loki_url
#
#     def write(self, message):
#         log_entry = {
#             "streams": [
#                 {
#                     "labels": '{app="vampire"}',
#                     "entries": [{"line": message.rstrip()}]
#                 }
#             ]
#         }
#         try:
#             requests.post(self.loki_url, data=json.dumps(log_entry), headers={"Content-Type": "application/json"}, timeout=0.5)
#         except Exception:
#             pass
#
#     def flush(self):
#         pass
#
# class ElasticHandler:
#     def __init__(self, es_url):
#         self.es_url = es_url
#
#     def write(self, message):
#         try:
#             # Преобразуем loguru message в JSON для Elasticsearch
#             log_doc = {"message": message.rstrip()}
#             requests.post(f"{self.es_url}/logs/_doc", data=json.dumps(log_doc), headers={"Content-Type": "application/json"}, timeout=0.5)
#         except Exception:
#             pass
#
#     def flush(self):
#         pass

logger.remove()
logger.add(sys.stdout, level="INFO")
# logger.add(LokiHandler("http://loki:3100/loki/api/v1/push"), level="INFO")
# logger.add(ElasticHandler("http://elasticsearch:9200"), level="INFO")
 
# TODO: интеграция с Grafana/Loki/Elasticsearch 