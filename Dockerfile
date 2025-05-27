
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to install dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory
COPY . .

# Create pdf_storage directory
RUN mkdir -p /app/pdf_storage

# Set environment variables
ENV PORT=8000

# Command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]