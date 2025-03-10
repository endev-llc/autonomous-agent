FROM python:3.10-slim

WORKDIR /app

# Copy the requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure the web directory exists and has proper permissions
RUN mkdir -p /app/web && chmod -R 755 /app/web

# Environment variables (override with docker-compose or at runtime)
ENV OPENAI_API_KEY="your-api-key-here"
ENV AGENT_GOAL="Discover a new law of physics by exploring theoretical inconsistencies in current models, seeking patterns in existing data, and proposing novel mathematical frameworks that could explain observed phenomena. Develop, test, and refine hypotheses through thought experiments and logical reasoning. Document your process, insights, and ultimately formulate a coherent new physical law or theory."

# Expose port for web interface
EXPOSE 8080

# Run the agent
CMD ["python", "src/main.py"]