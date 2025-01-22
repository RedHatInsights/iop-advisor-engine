import json
import os
import shutil
import traceback
from advisor_engine import config, loggers, foreman, content
from advisor_engine.insights_core_engine import install_rules, get_engine_results
import concurrent.futures

logger = loggers.engine_logging()
rule_content = content.get_rule_content()

executor = concurrent.futures.ProcessPoolExecutor(max_workers=config.WORKER_COUNT)


def setup_components():
    install_rules()


def resume_existing_archives():
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    for existing_archive in os.listdir(config.UPLOAD_DIR):
        logger.info(f'Found existing archive {existing_archive} to be processed.')
        process_background(os.path.join(config.UPLOAD_DIR, existing_archive))


def process_background(file, tries=1, error=None):
    def on_job_done(job):
        if job.cancelled():
            logger.info(f'Archive {file} cancelled.')
            return

        try:
            job.result()
            os.remove(file)
            logger.info(f'Archive {file} successfully processed after {tries} time(s).')
            #raise Exception(f'<some traceback error here>')
        except Exception as e:
            logger.error(f'Archive {file} failed due to {e}, trying again.')
            process_background(file, tries + 1, e)
            traceback.print_exc()

    if tries > config.MAX_ENGINE_RETRY:
        paths = file.split('/')
        failed_location = os.path.join(config.FAILED_DIR, paths[len(paths)-1])
        os.makedirs(config.FAILED_DIR, exist_ok=True)
        shutil.move(file, failed_location)
        logger.error(f'Archive {file} failed due to {error} after trying to process {config.MAX_ENGINE_RETRY} time(s).')
        logger.error(f'Archive {file} is being moved to {failed_location} for further analysis.')
    else:
        logger.info(f'Archive {file} is being processed {tries} time(s).')
        engine_job = executor.submit(process, file)
        engine_job.add_done_callback(on_job_done)


def process(file):
    engine_results = get_engine_results(file)
    store_results(engine_results)


def store_results(engine_results):
    system = engine_results['system']
    reports = engine_results['reports']

    logger.debug(system)
    logger.debug(reports)

    hits = []
    resolutions = []

    rules = []
    details = {}
    for report in reports:
        rule_id = report['rule_id']
        rule = rule_content.get(rule_id)
        #  If we don't have content for the rule hit we skip it.
        if not rule:
            continue
        if not rule['active']:
            continue
        hits.append({
            "title": rule['description'],
            "solution_url": f"https://access.redhat.com/node/{rule['node_id']}",
            "total_risk": int((rule['rec_likelihood'] + rule['rec_impact']) / 2),
            "likelihood": rule['rec_likelihood'],
            "publish_date": rule['publish_date'],
            "results_url": "Not available with on premises insights",
            "rule_id": rule_id,
        })
        for fix_type, playbook in rule['playbooks'].items():
            resolutions.append({
                "rule_id": rule_id,
                "description": playbook["name"],
                "needs_reboot": playbook["reboot_required"] == True,
                "resolution_risk": rule["resolution_risk"],
                "resolution_type": fix_type
            })
        #  This is a strange quirk of how foreman determines if a rule has a playbook available. foreman does not
        #  store rules that do not have a playbook remediation. It'd be great if foreman could change this so the
        #  user could see the manual remediation even if there is no playbook
        if rule["playbooks"]:
            rules.append(
                {
                    "rule_id": rule_id,
                    "description": rule["description"],
                    "category_name": rule["category"],
                    "impact_name": rule["impact_name"],
                    "summary": rule["summary"],
                    "generic": rule["generic"],
                    "reason": rule["reason"],
                    "total_risk": int((rule['rec_likelihood'] + rule['rec_impact']) / 2),
                    "reboot_required": rule["reboot_required"] == True,
                    "more_info": rule["more_info"],
                    "rating": 0
                }
            )
        details[rule_id] = report['details']
    foreman.store_advisor_hits(system['hostname'], system["system_id"], rules, resolutions, hits, details)


def shutdown():
    # Let the archives that are running complete but cancel ones in the queue
    executor.shutdown(wait=True, cancel_futures=True)
