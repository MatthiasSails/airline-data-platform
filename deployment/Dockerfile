FROM python:3.12
WORKDIR /app
COPY etl/requirements.txt .
RUN pip install -r requirements.txt
COPY etl/ .
RUN chmod +x run_bronze.sh run_silver.sh
