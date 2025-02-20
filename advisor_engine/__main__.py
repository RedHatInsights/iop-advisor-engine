import os
import signal
import uvicorn
from advisor_engine.endpoints import app, config
import advisor_engine.archive_processor as archive_processor
from advisor_engine import loggers

engine_logger = loggers.engine_logging()
api_logger = loggers.api_logging()

# Use TLS if cert exists.  See readme on how to create one.
tls_options = {}
if os.path.isfile('cert.pem') and os.path.isfile('key.pem'):
    tls_options['ssl_keyfile'] = 'key.pem'
    tls_options['ssl_certfile'] = 'cert.pem'

original_pid = os.getpid()


def signal_handler(sig, frame):
    if original_pid != os.getpid():
        return
    engine_logger.info(f'Shutdown signal received. Shutting down Engine...')
    api_logger.info(f'Shutdown signal received. Shutting down API...')
    archive_processor.shutdown()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

archive_processor.resume_existing_archives()
uvicorn.run(app, host=config.ADVISOR_ENGINE_BIND,
                 port=config.ADVISOR_ENGINE_PORT,
                 log_config=loggers.get_api_config(), **tls_options)
