# Autonomous Agent

An autonomous agent that can perform tasks and work toward a goal using a language model.

## Features

- Autonomous action cycles toward a defined goal
- Periodic reflection to improve strategy
- Memory system for maintaining context
- Web dashboard for monitoring the agent's operations

## Setup and Running

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Setting Up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

### Running with Docker

1. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

2. Start the agent using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Access the web dashboard at http://localhost:3000

4. View logs:
   ```bash
   docker-compose logs -f
   ```

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=your-openai-api-key-here
   ```

3. Run the agent:
   ```bash
   python src/main.py
   ```

4. Access the web dashboard at http://localhost:3000

## Web Dashboard

The web dashboard provides a visual interface to monitor the agent's operations:

- **Agent Identity**: Basic information about the agent
- **Current Memory**: The agent's current memory state
- **Activity Log**: Real-time log of the agent's activities
- **Latest Interaction**: Details of the most recent prompt and response

## Configuration

Edit `config.yaml` to customize the agent:

- `agent.name`: Name of the agent
- `agent.goal`: The goal the agent will work toward
- `agent.reflection_interval`: How often the agent performs reflection (in hours)
- `agent.action_interval`: How often the agent performs actions (in hours)
- `model.provider`: Language model provider (currently only "openai" is supported)
- `model.model_id`: The model ID to use (e.g., "gpt-4o-2024-08-06")
- `memory.max_tokens`: Maximum memory size in tokens

## Project Structure

- `src/`: Source code
  - `main.py`: Entry point
  - `agent.py`: Main agent class
  - `memory.py`: Memory management
  - `model_interface.py`: Interface to language model
  - `reflection.py`: Agent reflection capability
  - `web_server.py`: Web server for dashboard
- `web/`: Web dashboard files
- `data/`: Data storage (memory, logs)
- `config.yaml`: Agent configuration
- `Dockerfile` and `docker-compose.yml`: Docker configuration
