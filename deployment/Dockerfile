FROM python:3.12
WORKDIR /app
COPY etl/requirements.txt .
RUN pip install -r requirements.txt
COPY etl/ .
RUN chmod +x run_bronze.sh run_silver.sh

# The commit this image was built from, logged once when each loop starts. A green
# "redeployed" in Portainer has more than once left a container on old code; the log
# line shows what is actually running without a trip to GHCR. Kept last so a new
# commit does not invalidate the pip layer above.
ARG GIT_SHA=unknown
ENV GIT_SHA=$GIT_SHA
