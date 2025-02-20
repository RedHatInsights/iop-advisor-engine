import os, sys, subprocess
from advisor_engine import config, loggers
from insights.core import dr
from insights.core.evaluators import InsightsEvaluator
from insights.core.hydration import initialize_broker
from insights.core.archives import extract

engine_logger = loggers.engine_logging()

class Engine():
    def __init__(self):
        self.install_rules()
        self.setup_broker_and_components()


    def install_rules(self):
        engine_logger.info('Checking if custom rules have been installed...')
        if os.path.isdir(config.RULES_DIR):
            engine_logger.info('Custom rules directory exists. Installing custom rules.')
            wheel_files = [os.path.join(config.RULES_DIR, f) for f in os.listdir(config.RULES_DIR) if os.path.isfile(os.path.join(config.RULES_DIR, f))]
            engine_logger.info(f'Found rule wheel files to install: {wheel_files}')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', *wheel_files])


    def setup_broker_and_components(self):
        # Load the base insights-core specs
        engine_logger.info('Loading base insights-core components.')
        dr.load_components(
            'insights.specs.default',
            'insights.specs.insights_archive',
            continue_on_error=False
        )
        # Try to load additional components if they have been installed
        if len(config.RULES_COMPONENTS):
            engine_logger.info(f'Loading additional core components if installed: {config.RULES_COMPONENTS}')
            dr.load_components(*config.RULES_COMPONENTS, continue_on_error=False)
        else:
            engine_logger.warning('No RULES_COMPONENTS defined in config. '
                                  'Running Engine with no rule plugins.')


    def get_engine_results(self, file):
        with extract(
                file, timeout=10, extract_dir=config.UPLOAD_EXTRACTION_DIR
        ) as extraction:
            ctx, broker = initialize_broker(extraction.tmp_dir, broker=dr.Broker())
            with InsightsEvaluator(broker) as evaluator:
                dr.run({}, broker=broker)
                return evaluator.get_response()
