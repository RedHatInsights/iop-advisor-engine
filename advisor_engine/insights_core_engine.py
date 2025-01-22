from advisor_engine import config, loggers
import os, sys, subprocess

engine_logger = loggers.engine_logging()
loaded = False


def install_rules():
    engine_logger.info('Checking if custom rules have been installed...')
    if os.path.isdir(config.RULES_DIR):
        engine_logger.info('Custom rules directory exists. Installing custom rules.')
        try:
            wheel_files = [os.path.join(config.RULES_DIR, f) for f in os.listdir(config.RULES_DIR) if os.path.isfile(os.path.join(config.RULES_DIR, f))]
            engine_logger.info(f'Found rule wheel files to install: {wheel_files}')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *wheel_files])
        except Exception as e:
            engine_logger.warning('Exception installing custom rules:', e)


def get_engine_results(file):
    """
    This function takes in a path to an archive and returns a list of rule hits.

    The reason the imports are done lazily within the function is so that we can load in new rules at run time.
    The code is expected to be run by a worker from ProcessPoolExecutor(). This allows new workers to pick up the
    newest rules and insights_core code. If we did not do it lazily, then the ProcessPoolExcutor call to fork()
    would copy whatever modules were loaded during application start.
    """
    from insights.core import dr
    from insights.core.evaluators import InsightsEvaluator
    from insights.core.hydration import initialize_broker
    from insights.core.archives import extract
    global loaded
    if not loaded:
        # Load the base insights-core specs
        engine_logger.info('Loading base insights-core components.')
        dr.load_components(
            'insights.specs.default',
            'insights.specs.insights_archive',
            continue_on_error=False
        )
        # Try to load additional components if they have been installed
        if len(config.RULES_COMPONENTS):
            try:
                engine_logger.info('Loading additional core components if installed.')
                dr.load_components(*config.RULES_COMPONENTS)
            except Exception as e:
                engine_logger.warning('Exception loading additional components:', e)
        else:
            engine_logger.warning('No RULES_COMPONENTS defined in config. '
                                  'Running Engine with no rule plugins.')
        loaded = True

    with extract(
            file, timeout=10, extract_dir=config.UPLOAD_EXTRACTION_DIR
    ) as extraction:
        ctx, broker = initialize_broker(extraction.tmp_dir, broker=dr.Broker())
        with InsightsEvaluator(broker) as evaluator:
            dr.run({}, broker=broker)
            return evaluator.get_response()
