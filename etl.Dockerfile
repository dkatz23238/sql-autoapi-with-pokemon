FROM pokemonrestapp:latest
WORKDIR /usr/src/poketl
COPY etl.requirements.txt /usr/src/poketl/
RUN python -m pip install -r etl.requirements.txt
ADD etl /usr/src/poketl/
CMD ["python", "main.py"]