from loguru import logger

logger.add("logs/app.log", rotation="10 MB")
 
# TODO: интеграция с Grafana/Loki/Elasticsearch 