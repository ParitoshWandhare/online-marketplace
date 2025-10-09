# 1. Start with an official Python base image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first to leverage Docker's caching
COPY requirements.txt .

# 4. Install the Python dependencies (force latest pip + correct versions)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy your application code into the container
COPY . .

# 6. Expose the port the app runs on
EXPOSE 8000

# 7. Define the command to run your app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
