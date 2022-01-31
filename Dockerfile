FROM python:3.9

RUN pip install requests && \
    pip install prometheus_client

ADD exporter.py /

EXPOSE 9886/tcp

CMD [ "python", "-u", "./exporter.py" ]
