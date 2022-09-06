FROM python:3-alpine
WORKDIR /root/

RUN python3 -m pip install pyiotown==0.4.0

COPY ./parser .

CMD python3 run.py
