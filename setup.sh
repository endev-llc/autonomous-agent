#!/bin/bash
# Setup script for the autonomous agent

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Please provide your OpenAI API key:"
    read -s OPENAI_API_KEY
    export OPENAI_API_KEY
fi

# Create .env file for Docker
echo "Creating .env file for Docker..."
cat > .env << EOL
OPENAI_API_KEY=$OPENAI_API_KEY
AGENT_GOAL="Your goal here - replace with your actual goal"
EOL

echo "Building Docker image..."
docker build -t autonomous-agent .

echo "Setup complete!"
echo "You can now run the agent with the provided run command"