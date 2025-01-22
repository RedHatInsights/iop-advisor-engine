import apypie
import itertools
import json
from advisor_engine import config, loggers

logger = loggers.engine_logging()

def get_host_names(system_ids):
    hosts = get_hosts_details(system_ids)
    return [host["name"] for host in hosts]

def get_advisor_report_details(insights_id):
    hosts = get_hosts_details([insights_id])
    if len(hosts) == 0:
        return ""
    return hosts[0]["insights_hit_details"]

def get_api():
    return apypie.ForemanApi(
        uri=config.FOREMAN_URL,
        verify_ssl=config.CLIENT_CA_CERT,
        client_cert=config.ADVISOR_CLIENT_CERT,
        client_key=config.ADVISOR_CLIENT_KEY
    )

def get_hosts_details(system_ids, batch_size = 1000):
    api = get_api()
    results = []
    for batch in itertools.batched(system_ids, batch_size):
        try:
            results.extend(api.resource_action('advisor_engine', 'host_details', params={"host_uuids": batch}))
        except Exception as e:
            logger.error("An error occurred:", e)

    return results

def store_advisor_hits(host_name, host_uuid, rules, resolutions, hits, details):
    api = get_api()

    # Request Payload
    data = {
        "host_name": host_name,  # Required field,
        "host_uuid": host_uuid,
        "payload": {
            "resolutions": resolutions,
            "rules": rules,
            "hits": hits,
            "details": json.dumps(details)
        }
    }

    try:
        api.resource_action('advisor_engine', 'upload_hits', params=data)
    except Exception as e:
        logger.error("An error occurred:", e)
