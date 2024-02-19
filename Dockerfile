FROM python:3.10.12-slim

WORKDIR /app

# Copy the entire project
COPY . .

# Install the grobid_client_python package and other requirements
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git && \
    pip install -r requirements.txt --no-cache-dir 

EXPOSE 8000

CMD ["chainlit", "run", "app.py", "-h"]