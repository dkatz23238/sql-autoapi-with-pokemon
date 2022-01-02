
FROM python:3.8.12-slim-buster
WORKDIR /usr/src/restapp/
RUN apt-get update
RUN apt-get install -y default-libmysqlclient-dev python3-mysqldb
COPY requirements.txt /usr/src/restapp/
RUN python3.8 -m pip install -r requirements.txt
ADD . /usr/src/restapp/
EXPOSE 8000
WORKDIR /usr/src
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "restapp.app:app", "-b", "0.0.0.0:8000", "--workers=4"]
