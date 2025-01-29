import os
import socket

# Advisor Engine API
ADVISOR_ENGINE_BIND = os.environ.get('ADVISOR_ENGINE_BIND', '127.0.0.1')
ADVISOR_ENGINE_PORT = int(os.environ.get('ADVISOR_ENGINE_PORT', 24443))

# Foreman API
ADVISOR_CLIENT_KEY = os.environ.get("ADVISOR_CLIENT_KEY", "client_key.pem")
ADVISOR_CLIENT_CERT = os.environ.get("ADVISOR_CLIENT_CERT", "client_cert.pem")
CLIENT_CA_CERT = os.environ.get("FOREMAN_CA_CERT", "client_ca.pem")
FOREMAN_URL = os.environ.get("FOREMAN_URL", f"https://{socket.getfqdn()}")

# Static Content for Rules, Plugins, and Content
STATIC_CONTENT_DIR = os.environ.get('STATIC_CONTENT_DIR', 'static')
RULES_DIR = os.environ.get('RULES_DIR', 'static/rules')
RULES_COMPONENTS = os.environ.get('RULES_COMPONENTS').split(',') if os.environ.get('RULES_COMPONENTS','') != '' else []

# CPU
WORKER_COUNT = os.environ.get('WORKER_COUNT', None)  # None defaults to number of CPU cores

# Uploads
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', 'uploads')
FAILED_DIR = os.environ.get('FAILED_DIR', 'failed')
MAX_ENGINE_RETRY = os.environ.get('MAX_ENGINE_RETRY', 3)
UPLOAD_EXTRACTION_DIR = os.environ.get('UPLOAD_EXTRACTION_DIR', '/tmp')

# Logging
SIMPLE_LOGS = os.environ.get('SIMPLE_LOGS', '').lower() == 'true'
STDOUT_LOG_LEVEL = os.environ.get('STDOUT_LOG_LEVEL', 'WARNING')
LOG_DIR = os.environ.get('LOG_DIR', 'logs')
ENGINE_LOG_FILE = os.path.join(LOG_DIR, os.environ.get('ENGINE_LOG_FILE', 'iop-advisor-engine.log'))
ENGINE_LOG_LEVEL = os.environ.get('ENGINE_LOG_LEVEL', 'INFO')
ENGINE_MAX_BYTES = os.environ.get('ENGINE_MAX_BYTES', 10000)
ENGINE_BACKUP_COUNT = os.environ.get('ENGINE_BACKUP_COUNT', 5)
API_LOG_FILE = os.path.join(LOG_DIR, os.environ.get('API_LOG_FILE', 'iop-advisor-api.log'))
API_LOG_LEVEL = os.environ.get('API_LOG_LEVEL', 'INFO')
API_MAX_BYTES = os.environ.get('API_MAX_BYTES', 10000)
API_BACKUP_COUNT = os.environ.get('API_BACKUP_COUNT', 5)
FILE_LOGGING = os.environ.get('FILE_LOGGING', '').lower() == 'true'

# Toggle file logging or stdout only
if FILE_LOGGING:
    os.makedirs(LOG_DIR, exist_ok=True) # Ensure logging directory exists
    LOGGING_CONFIG = { 
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'simple': {
                'format': '<%(asctime)s> - %(levelname)s - %(message)s'
            },
            'logstash': { 
                'class': 'logstash_formatter.LogstashFormatter'
            },
        },
        'handlers': { 
            'stdout': { 
                'level': STDOUT_LOG_LEVEL,
                'formatter': 'simple' if SIMPLE_LOGS else 'logstash',
                'class': 'logging.StreamHandler'
            },
            'engine_file': {
                'level': ENGINE_LOG_LEVEL,
                'formatter': 'simple' if SIMPLE_LOGS else 'logstash',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': ENGINE_LOG_FILE,
                'maxBytes': ENGINE_MAX_BYTES,
                'backupCount': ENGINE_BACKUP_COUNT
            },
            'api_file': {
                'level': API_LOG_LEVEL,
                'formatter': 'simple' if SIMPLE_LOGS else 'logstash',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': API_LOG_FILE,
                'maxBytes': API_MAX_BYTES,
                'backupCount': API_BACKUP_COUNT
            }
        },
        'loggers': {
            'engine': {
                'handlers': ['stdout', 'engine_file'],
                'level': ENGINE_LOG_LEVEL,
                'propagate': False
            },
            'api': {
                'handlers': ['stdout', 'api_file'],
                'level': API_LOG_LEVEL,
                'propagate': False
            },
            'uvicorn': {
                'handlers': ['stdout', 'api_file'],
                'level': API_LOG_LEVEL,
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['stdout', 'api_file'],
                'level': API_LOG_LEVEL,
                'propagate': False
            },
            'uvicorn.error': {
                'handlers': ['stdout', 'api_file'],
                'level': API_LOG_LEVEL,
                'propagate': False
            }
        } 
    }
else:
    LOGGING_CONFIG = { 
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'simple': {
                'format': '<%(levelname)s> - %(asctime)s - %(message)s'
            }
        },
        'handlers': { 
            'stdout': { 
                'level': STDOUT_LOG_LEVEL,
                'formatter': 'simple',
                'class': 'logging.StreamHandler',
            }
        },
        'loggers': {
            'engine': {
                'handlers': ['stdout'],
                'level': STDOUT_LOG_LEVEL,
                'propagate': False
            },
            'api': {
                'handlers': ['stdout'],
                'level': STDOUT_LOG_LEVEL,
                'propagate': False
            },
            'uvicorn': {
                'handlers': ['stdout'],
                'level': STDOUT_LOG_LEVEL,
                'propagate': False
            },
            'uvicorn.access': {
                'handlers': ['stdout'],
                'level': STDOUT_LOG_LEVEL,
                'propagate': False
            },
            'uvicorn.error': {
                'handlers': ['stdout'],
                'level': STDOUT_LOG_LEVEL,
                'propagate': False
            }
        } 
    }