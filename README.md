# 🦖 Jobzilla

> AI-powered job matching platform with multi-agent debates using LangGraph

[![CI](https://github.com/your-org/jobzilla/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/jobzilla/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

- **Multi-Agent Debate System**: Recruiter vs Coach agents debate your fit for jobs
- **MCP Server Architecture**: Model Context Protocol servers for GitHub and job market data
- **Semantic Job Matching**: Pinecone-powered vector search with OpenAI embeddings
- **Cover Letter Generation**: AI-generated letters informed by the debate
- **Skill Gap Analysis**: Personalized learning roadmaps
- **Proactive Headhunting**: Daily job matching via Airflow DAGs

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend                        │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                         FastAPI Backend                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   LangGraph Agent Pipeline               │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │    │
│  │  │ Profile  │→ │Recruiter │→ │  Coach   │→ │  Judge  │  │    │
│  │  │ Parser   │  │ (Critic) │  │(Advocate)│  │(Arbiter)│  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
│  MCP Server   │         │  MCP Server   │         │   Pinecone    │
│ GitHub Context│         │  Job Market   │         │ Vector Store  │
└───────────────┘         └───────────────┘         └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- API Keys: OpenAI, Pinecone, GitHub Token

### Setup

1. **Clone and configure**
   ```bash
   git clone https://github.com/your-org/jobzilla.git
   cd jobzilla
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start all services**
   ```bash
   make up
   # or
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Airflow: http://localhost:8080

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run backend
cd backend && uvicorn app.main:app --reload

# Run frontend (new terminal)
cd frontend && streamlit run app.py

# Run MCP servers (new terminals)
cd mcp_servers/github-context && python server.py
cd mcp_servers/job-market && python server.py
```

## 📁 Project Structure

```
killmatch-agentic-suite/
├── backend/              # FastAPI + LangGraph agents
│   ├── app/
│   │   ├── api/         # REST endpoints
│   │   ├── agents/      # LangGraph nodes & edges
│   │   ├── models/      # Pydantic schemas
│   │   └── services/    # Business logic
├── frontend/             # Streamlit UI
│   ├── app.py
│   └── components/      # Reusable UI components
├── mcp_servers/          # MCP protocol servers
│   ├── github-context/  # GitHub profile analysis
│   └── job-market/      # Job search & intel
├── airflow/              # Orchestration DAGs
│   └── dags/
└── docs/                 # Documentation
```

## 🤖 Agent Pipeline

The core matching uses a multi-agent debate pattern:

1. **Profile Parser**: Extracts skills from resume + GitHub
2. **Recruiter Agent**: Identifies concerns/weaknesses (devil's advocate)
3. **Coach Agent**: Highlights strengths (candidate advocate)
4. **Judge Agent**: Weighs arguments, provides final verdict
5. **Skill Gap Agent**: Identifies missing skills with learning paths
6. **Cover Writer**: Generates debate-informed cover letters
7. **Improvement Agent**: Suggests profile enhancements

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/profile` | POST | Upload resume + GitHub |
| `/api/v1/match` | POST | Run agent matching pipeline |
| `/api/v1/cover-letter` | POST | Generate cover letter |
| `/api/v1/analytics/{user_id}` | GET | User dashboard data |
| `/api/v1/headhunter/{user_id}` | GET | Proactive recommendations |

## ⚙️ Configuration

Key environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM + embeddings |
| `PINECONE_API_KEY` | Pinecone vector database key |
| `GITHUB_TOKEN` | GitHub personal access token |
| `TAVILY_API_KEY` | Tavily API for company intel |

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test suites
pytest backend/tests/unit -v
pytest backend/tests/integration -v

# Run with coverage
pytest --cov=backend/app --cov-report=html
```

## 📊 Evaluation

Compare agent-based matching vs naive cosine similarity:

```bash
cd eval
python run_benchmark.py
```

## 🚢 Deployment

### Backend (GCP Cloud Run)
```bash
gcloud run deploy killmatch-backend --source ./backend
```

### Frontend (Streamlit Cloud)
1. Connect repository to Streamlit Cloud
2. Set `frontend/app.py` as entry point
3. Configure secrets in dashboard

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

Built with ❤️ using LangGraph, FastAPI, and Streamlit
