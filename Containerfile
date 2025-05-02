FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Can override this when you run the container.
ENV ROBOFLOW_API_KEY="132cxQxyrOVmPD63wJrV"
ENV BASE_DIR=/app/data

# Runs on container start
CMD ["python", "seals_counter_cli.py"]