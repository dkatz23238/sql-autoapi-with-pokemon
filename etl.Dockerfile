FROM restapp:latest
WORKDIR /usr/src/poketl
COPY etl.requirements.txt /usr/src/poketl/
RUN python -m pip install -r etl.requirements.txt