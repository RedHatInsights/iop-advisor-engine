FROM registry.access.redhat.com/ubi9/python-312
USER 1001

COPY pyproject.toml .
RUN mkdir advisor_engine
RUN pip install .

COPY special_playbooks special_playbooks
COPY advisor_engine advisor_engine

CMD python -m advisor_engine
