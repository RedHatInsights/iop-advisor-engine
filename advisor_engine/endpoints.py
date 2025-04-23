import json
import os
import os.path
from uuid import UUID
import aiofiles
from fastapi import UploadFile, File, Body, FastAPI, Form, status, Request, HTTPException
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from advisor_engine import foreman, config, content, loggers
from advisor_engine.archive_processor import process_background

rules = content.get_rule_content()
api_logging = loggers.api_logging()

# Create the static directory if it does not exist
if not os.path.exists(config.STATIC_CONTENT_DIR):
    os.makedirs(config.STATIC_CONTENT_DIR)


def handle_module_update_router():
    return {'url': '/release'}


def handle_system_get_legacy():
    return {'unregistered_at': None}


def handle_system_get(insights_id: UUID = '00000000-0000-0000-0000-000000000000'):
    return {"total": 1, "results": [{"id": insights_id}]}

def handle_system_exists(insights_id: UUID = '00000000-0000-0000-0000-000000000000'):
    return {"id": insights_id}

async def handle_insights_archive(request: Request,
                                  file: Optional[UploadFile] = File(None),
                                  test: str=Form(None)):
    # insights-client --test-connection
    # Just want to send back a 200 for the Client/Satellite
    if test: return Response(status_code=status.HTTP_200_OK)
    else:
        content_length = int(request.headers.get('content-length'))
        if ((content_length is None) or
            (content_length > config.ADVISOR_ENGINE_MAX_CONTENT_LENGTH)):
            return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                content={"detail": "Request body too large or missing."})

        async with aiofiles.tempfile.NamedTemporaryFile('wb', dir=config.UPLOAD_DIR,
                                                              delete=False,
                                                              suffix='.tar.gz') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
        process_background(out_file.name)
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


def handle_status():
    config_var_dir = dir(config)
    config_vars = {}
    for config_var in config_var_dir:
        if (not config_var.startswith('__') and
                config_var not in ['os', 'socket']):
            config_vars[config_var] = getattr(config, config_var)

    current_count = (len([name for name in os.listdir(config.UPLOAD_DIR)]) 
                        if os.path.exists(config.UPLOAD_DIR) else f'{config.UPLOAD_DIR} dir not found.')
    failed_count = (len([name for name in os.listdir(config.FAILED_DIR)])
                        if os.path.exists(config.FAILED_DIR) else f'{config.FAILED_DIR} dir not found.')

    return {
        'engine': 'up',  # Engine assumed up. Will fail on initialization if not
        'failed': failed_count,
        'current': current_count,
        'config': config_vars
    }

  
def handle_api_ping():
    # Just want to send back a 200 for the Client/Satellite
    return Response(status_code=status.HTTP_200_OK)


class HeaderSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check number of headers
        if len(request.headers) > config.ADVISOR_ENGINE_MAX_HEADER_FIELDS:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Too many headers"})
        
        # Check header size
        for k, v in request.headers.items():
            if len(k) + len(v) > config.ADVISOR_ENGINE_MAX_HEADER_FIELD_SIZE:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                    content={"detail": "Header field too large"})
        
        return await call_next(request)


app = FastAPI()

app.add_middleware(HeaderSizeLimitMiddleware)

app.post('/api/ingress/v1/upload/{path:path}')(handle_insights_archive)
app.post('/r/insights/uploads/{path:path}')(handle_insights_archive)
app.get('/api/module-update-router/v1/channel')(handle_module_update_router)
app.mount('/r/insights/v1/static/release/', StaticFiles(directory=config.STATIC_CONTENT_DIR), name='static')
app.get('/r/insights/v1/systems/{path:path}')(handle_system_get_legacy)
app.get('/api/inventory/v1/hosts')(handle_system_get)
app.get('/api/inventory/v1/host_exists')(handle_system_exists)
app.post('/api/remediations/v1/playbook')(handle_playbook)
app.get('/api/remediations/v1/diagnosis/{insights_id}')(handle_diagnosis)
app.get('/status')(handle_status)
app.get('/api/apicast-tests/ping')(handle_api_ping)
