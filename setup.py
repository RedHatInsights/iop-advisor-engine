from setuptools import find_packages, setup


requirements = [
    "apypie>=0.6.0",
    "setuptools",
    "fastapi",
    "python-multipart",
    "uvicorn",
    "aiofiles",
    'logstash-formatter',
    'insights-core'
]

setup(
    name="iop-advisor-engine",
    version="0.1",
    url="https://github.com/RedHatInsights/iop-advisor-engine",
    package_dir={"": "advisor_engine"},
    install_requires=requirements
)
