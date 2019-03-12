#
# container docker pour dila2sql
#
# https://github.com/SocialGouv/dila2sql
#
# build     : `docker build -t dila2sql .`
#

FROM python:alpine

RUN apk add --update git gcc python-dev libxml2-dev libxslt-dev musl-dev wget libarchive libarchive-dev postgresql-dev

RUN python -m ensurepip

# preload requirements so we benefit the docker image caching layer
RUN pip install libarchive-c lxml tqdm psycopg2-binary

ENV LEGI_PATH /app

WORKDIR $LEGI_PATH

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
