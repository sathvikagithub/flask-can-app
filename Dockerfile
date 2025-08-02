# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy app code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir flask flask-cors mysql-connector-python

# Expose Flask port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
