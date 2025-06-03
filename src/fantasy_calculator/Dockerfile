FROM python:3.11-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY src/fantasy_calculator/ .

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
