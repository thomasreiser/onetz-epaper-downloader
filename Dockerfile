FROM python:3.8-slim AS onetz

LABEL maintainer="reiser.thomas@gmail.com"

VOLUME /config
VOLUME /newspaper

RUN pip install --no-cache-dir requests beautifulsoup4 fake-useragent workalendar

ADD newspaper.py /

CMD [ "python", "./newspaper.py", "-c", "/config/newspaper.json" ]
