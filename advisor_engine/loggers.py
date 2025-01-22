import logging
import logstash_formatter
from advisor_engine import config, loggers

logging.config.dictConfig(config.LOGGING_CONFIG)


def engine_logging():
   return logging.getLogger('engine')


def api_logging():
   return logging.getLogger('api')


def get_api_config():
   return config.LOGGING_CONFIG
