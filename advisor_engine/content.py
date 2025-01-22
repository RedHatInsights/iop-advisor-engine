import os, json
from advisor_engine import config, loggers

engine_logger = loggers.engine_logging()
content_path = os.path.join(config.STATIC_CONTENT_DIR, 'content.json')
rule_content = None


def get_rule_content():
    global rule_content
    if rule_content is None:
        if os.path.isfile(content_path):
            try:
                with open(content_path, 'r') as file:
                    rule_content = json.load(file)
            except Exception as e:
                engine_logger.warning('No rule content found: ',e)
        else:
            engine_logger.warning('No rule content content.json file found. ' 
                                  'Engine running with no rule content.')
            rule_content = {}
    return rule_content
