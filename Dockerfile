FROM python:3-alpine
WORKDIR /root/

RUN python3 -m pip install pyiotown==0.3.3.dev1

COPY ./parser .

CMD python3 run.py
