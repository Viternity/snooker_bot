# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script and database into the container at /app
COPY bot.py .
COPY league_database.sqlite .

# Define environment variable for the token (it will be passed during runtime)
ENV DISCORD_TOKEN=${DISCORD_TOKEN}

# Run bot.py when the container launches
CMD ["python", "bot.py"]

