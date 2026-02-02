# Use a newer official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install PostgreSQL system libs
# RUN apt-get update && apt-get install -y \
#     libpq-dev gcc \
#     && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 5000

# Run Flask
CMD ["python", "server.py"]




# Notes:
# Creates a Docker image of your backend (packages your code + dependencies).
# docker build -t mapmarket-backend:latest .

# Runs that image in a container
# docker run -p 5000:5000 mapmarket-backend:latest
