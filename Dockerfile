FROM python:3.10-slim

WORKDIR /app

# Copy the requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Environment variables (override with docker-compose or at runtime)
ENV OPENAI_API_KEY="your-api-key-here"
ENV AGENT_GOAL="Default goal: Analyze data and provide insights"

# Run the agent
CMD ["python", "src/main.py"]