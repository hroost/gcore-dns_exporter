FROM python:3.12-slim

RUN pip install pip --upgrade && \
    pip install requests && \
    pip install prometheus_client

ADD exporter.py /

EXPOSE 9886/tcp

CMD [ "python", "-u", "./exporter.py" ]
