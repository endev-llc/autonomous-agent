# Physics Article Curator Agent

An autonomous agent that continuously finds, summarizes, categorizes, and scores the latest physics articles from across the web.

## Features

- **Autonomous Operation**: Runs 24/7 in a Docker container
- **Web Search**: Finds the latest physics articles from reputable sources
- **Article Processing**:
  - Summarizes article content
  - Categorizes with 3 keywords for easy searching
  - Scores articles based on significance and reader value
- **Local Database**: Stores all article data for later retrieval
- **Web Interface**: Simple UI to browse and search the collected articles

## Setup

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Configuration

1. Copy the example environment file and add your API key:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file to add your OpenAI API key
   
3. (Optional) Modify the `config.yaml` file to adjust agent behavior

### Running the Agent

```bash
# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

## Web Interface

Once running, you can access the web interface at:
```
http://localhost:5000
```

## Database

Article data is stored in a SQLite database at `./data/articles.db`

## Customization

You can customize the agent's behavior by editing the `config.yaml` file:

- `agent.goal`: The primary objective of the agent
- `agent.action_interval`: How often the agent searches for new articles (hours)
- `model.provider` and `model.model_id`: Change the AI model being used
- `model.web_search_enabled`: Toggle web search capability
- `model.max_search_tokens`: Maximum tokens for search operations
- `model.max_analysis_tokens`: Maximum tokens for article analysis
- `memory.max_tokens`: Maximum tokens for agent memory

## Architecture

- `src/agent.py`: Core agent logic for finding and processing articles
- `src/database.py`: Database operations for storing and retrieving articles
- `src/main.py`: Main application entry point
- `src/web_server.py`: Web interface for browsing articles

## License

MIT
