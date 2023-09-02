FROM python:3-alpine
WORKDIR /root/

RUN apk add --no-cache nodejs
RUN python3 -m pip install redis
RUN python3 -m pip install pillow
RUN python3 -m pip install pyiotown==0.4.3

COPY ./parser .

CMD [ "python3", "-u", "run.py", "--url", "$IOTOWN_URL", "--user", "$IOTOWN_USER", "--token", "$IOTOWN_TOKEN", "--dry", "$DRY_RUN" ]
