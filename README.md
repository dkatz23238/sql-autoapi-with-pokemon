# Automatic SQL API Generation w/ Pokemon Example

First of all make sure you use `python` 3.8 and install the packages in `requirements.txt`.

## Quickstart

### Build and run server
```sh
docker-compose down && docker-compose rm;
python api_builder.py;
docker-compose build;
docker-compose up -d;
sleep 90;
python make_tables.py;
python make_views.py;
python perform_data_seed.py;
```

## Instructions

### 1) `models.py` and `queries`

Populate models.py with valid data model and queries with sql views that should be served through the API.

### 2) Quickstart

Run the quickstart script