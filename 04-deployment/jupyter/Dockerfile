FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        jupyterlab==4.5.7 \
        pandas==3.0.3 \
        numpy==2.4.5 \
        matplotlib \
        plotly \
        pymongo==4.17.0 \
        requests==2.34.0 \
        python-dotenv==1.2.2 \
        psycopg2-binary==2.9.12 \
        ipywidgets

WORKDIR /workspace
EXPOSE 8888

CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--notebook-dir=/workspace"]
