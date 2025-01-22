import json
import os
from uuid import UUID
import aiofiles
from fastapi import UploadFile, File, Body, FastAPI
from fastapi.responses import Response, FileResponse

from advisor_engine import foreman, config, content
from advisor_engine.archive_processor import process_background

rules = content.get_rule_content()

def handle_module_update_router():
    return {'url': '/release'}


def handle_system_get_legacy():
    return {'unregistered_at': None}


def handle_system_get(insights_id: UUID = '00000000-0000-0000-0000-000000000000'):
    return {"total": 1, "results": [{"id": insights_id}]}


def handle_egg():
    return FileResponse(os.path.join(config.STATIC_CONTENT_DIR, 'insights-core.egg'), media_type="application/octet-stream")


def handle_egg_asc():
    return FileResponse(os.path.join(config.STATIC_CONTENT_DIR, 'insights-core.egg.asc'))


async def handle_insights_archive(file: UploadFile = File(...)):
    file_location = os.path.join(config.UPLOAD_DIR, file.filename)
    async with aiofiles.open(file_location, 'wb') as out_file:
        while content := await file.read(1024 * 1024):
            await out_file.write(content)
    process_background(file_location)
    return {'message': 'File uploaded successfully'}


def handle_playbook(post_data=Body(...)):
    playbook = "---\n"
    plays = ""
    report_hosts = set()
    reboot_hosts = set()
    all_hosts = set()
    for issue in post_data['issues']:
        host_names = foreman.get_host_names(issue['systems'])
        rule_id = issue["id"].split(':')[1]
        fix_type = issue['resolution']
        play = rules[rule_id]['playbooks'][fix_type]['text'].replace('{{HOSTS}}', ",".join(host_names))
        if 'insights_report' in play:
            report_hosts.update(host_names)
        if 'insights_needs_reboot' in play:
            reboot_hosts.update(host_names)
        all_hosts.update(host_names)
        plays += play

    if report_hosts:
        with open('special_playbooks/diagnosis.yml', 'r') as f:
            playbook += f.read().replace('{{HOSTS}}', ",".join(report_hosts))

    playbook += plays

    if reboot_hosts:
        with open('special_playbooks/reboot.yml', 'r') as f:
            playbook += f.read().replace('{{HOSTS}}', ",".join(reboot_hosts))

    with open('special_playbooks/postRunCheckIn.yml', 'r') as f:
        playbook += f.read().replace('{{HOSTS}}', ",".join(all_hosts))
    return Response(content=playbook, media_type='text/vnd.yaml; charset=utf-8')


def handle_diagnosis(insights_id):
    details = foreman.get_advisor_report_details(insights_id)

    return {
        "id": insights_id,
        "insights_id": insights_id,
        "details": json.loads(details)
    }


app = FastAPI()

app.post('/api/ingress/v1/upload/{path:path}')(handle_insights_archive)
app.post('/r/insights/uploads/{path:path}')(handle_insights_archive)
app.get('/api/module-update-router/v1/channel')(handle_module_update_router)
app.get('/r/insights/v1/static/release/insights-core.egg.asc')(handle_egg_asc)
app.get('/r/insights/v1/static/release/insights-core.egg')(handle_egg)
app.get('/r/insights/v1/systems/{path:path}')(handle_system_get_legacy)
app.get('/api/inventory/v1/hosts')(handle_system_get)
app.post('/api/remediations/v1/playbook')(handle_playbook)
app.get('/api/remediations/v1/diagnosis/{insights_id}')(handle_diagnosis)
