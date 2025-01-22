# iop-advisor-engine


### Setup Environment and Libraries
```bash
python -m venv venv
source venv/bin/activate
pip install .
```

### Setup Rules and Content
Get the required rules and content. Copy or move the generated "static" folder
into the top level folder for iop-advisor-engine. Or optionally define the
`STATIC_CONTENT_DIR`, `RULES_DIR`, and `RULES_COMPONENTS` environment variables.
Rule development documentation can be found on the insights-core repository
located at https://github.com/RedHatInsights/insights-core.


### Engine Rules, Plugins, and Content Components
All content should be read from a "static" folder mounted and specified in the podman-compose 
file if needed and paired via the `STATIC_CONTENT_DIR`, `RULES_DIR`, and `RULES_COMPONENTS` 
environment variables. If new content is added after the Engine is running, it will need to be restarted.


### Rules Disclaimer
There should be a `static` folder with `content.json` containing a set of rules, 
and optional plugins to install. The Engine will still run if these are not present.


### Run the tests
```bash
pip install httpx
python -m unittest discover -s ./tests/unit 
```

### Start the Engine
```bash
python -m advisor_engine
```

### Upload against the Engine
Generate a system archive to be tested and upload it to the Engine.
```
curl -F "file=@./sample_archive.tar.gz" 
-H "x-rh-request_id: testupload" 
http://127.0.0.1:24443/api/ingress/v1/upload/ -v -k
```

### TLS
(Optional)If you want to use TLS, run the following command to generate a cert
```
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out cert.pem -subj "/CN=192.168.122.1"
```
Copy the cert.pem to the server to the following locations
* `/etc/pki/ca-trust/source/anchors/rh_cert-api_chain.pem`
 
and run 
```
update-ca-trust enable
update-ca-trust extract
update-ca-trust
```


### podman instructions
```bash
podman build --tag iop_advisor_engine .
podman run -p 24443:24443 iop_advisor_engine
```


### podman-compose
Note: You will need to edit the podman-compose file for the iop_advisor_engine declaration to point it
to the appropriate static content folder. See rule documentation and steps above.
```bash
podman-compose up -d
```
