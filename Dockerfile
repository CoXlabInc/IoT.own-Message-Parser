FROM python:3-alpine
WORKDIR /root/

RUN apk add --no-cache nodejs
RUN python3 -m pip install redis
RUN python3 -m pip install numpy
RUN python3 -m pip install pyiotown==0.6.4.dev2

COPY ./parser .

CMD [ "python3", "-u", "run.py", "--url", "$IOTOWN_URL", "--user", "$IOTOWN_USER", "--token", "$IOTOWN_TOKEN", "--dry", "$DRY_RUN" ]
