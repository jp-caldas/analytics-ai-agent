# Analytics AI Agent

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-orange.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple.svg)](https://www.langchain.com/langgraph)
[![GCP](https://img.shields.io/badge/Cloud%20Run-GCP-4285F4.svg)](https://cloud.google.com/run)
[![n8n](https://img.shields.io/badge/n8n-workflow-red.svg)](https://n8n.io/)

An AI-powered analytics agent that converts natural language questions into SQL, queries Google Analytics 4 data on BigQuery, and returns human-friendly answers — all through a chat interface.

Built with **FastAPI**, **LangChain**, **LangGraph**, and **OpenAI**, deployed on **Cloud Run** and integrated with **n8n** for conversational workflows.

---

## Architecture

```
User Question (natural language)
        │
        ▼
┌─────────────────────────────────────┐
│         n8n Chat Trigger            │
│  (when chat message received)       │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│     HTTP Request → Cloud Run        │
│  POST /v1/chat-ga4                  │
│  {"question": "..."}                │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│     FastAPI + LangGraph Agent       │
│                                     │
│  ┌─────────────┐                   │
│  │ generate_sql │ ← LLM (GPT-4o)   │
│  └──────┬──────┘                   │
│         ▼                          │
│  ┌─────────────┐                   │
│  │ execute_sql  │ → BigQuery       │
│  └──────┬──────┘                   │
│         ▼                          │
│  ┌─────────────┐                   │
│  │ should_retry │ ← max 3 attempts│
│  └─────────────┘                   │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  n8n Basic LLM Chain (GPT-4o-mini) │
│  (humanizes response in Portuguese) │
└─────────────────────────────────────┘
        │
        ▼
   User receives answer
```

## Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (Python 3.11) |
| **AI Orchestration** | LangChain + LangGraph |
| **LLM** | OpenAI GPT-4o (SQL generation), GPT-4o-mini (response formatting) |
| **Database** | Google BigQuery (GA4 public dataset) |
| **Deployment** | Google Cloud Run (containerized) |
| **Chat Interface** | n8n workflow (webhook + LLM chain) |

## Project Structure

```
analytics-ai-agent/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI server with /v1/chat-ga4 endpoint
│   ├── graph.py         # LangGraph workflow (generate SQL → execute → retry)
│   └── context.py       # GA4 dataset context prompt
├── .dockerignore
├── .env.example         # Environment variables template
├── .gitignore
├── Dockerfile           # Container image for Cloud Run
├── n8n-workflow.json    # n8n workflow export (chat + LLM integration)
├── README.md
└── requirements.txt
```

## How It Works

1. **User asks a question** in natural language via the n8n chat interface
2. **n8n sends a POST** request to the Cloud Run endpoint
3. **LangGraph workflow** executes:
   - `generate_sql` — GPT-4o generates a SQL query based on the question + GA4 dataset context
   - `execute_sql` — Runs a dry-run, then executes the query on BigQuery
   - `should_retry` — If the query fails, retries up to 3 times with the error as feedback
4. **n8n formats the response** using GPT-4o-mini, translating raw data into a clear, human-friendly answer
5. **User receives** the interpreted answer with the SQL query shown when relevant

## Local Setup

### Prerequisites
- Python 3.11+
- Google Cloud service account with BigQuery access
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/jp-caldas/analytics-ai-agent.git
cd analytics-ai-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials:
#   GOOGLE_APPLICATION_CREDENTIALS=path/to/gcp-key.json
#   OPENAI_API_KEY=sk-proj-...
```

### Run Locally

```bash
# Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Test the endpoint
curl -X POST http://localhost:8080/v1/chat-ga4 \
  -H "Content-Type: application/json" \
  -d '{"question":"How many unique users in January 2021?"}'
```

## Deployment

### Cloud Run

```bash
# Build and push the image
gcloud builds submit --tag gcr.io/YOUR-PROJECT/ga4-agent

# Deploy to Cloud Run
gcloud run deploy ga4-agent \
  --image gcr.io/YOUR-PROJECT/ga4-agent \
  --region us-central1 \
  --port 8080 \
  --allow-unauthenticated \
  --min-instances 0 \
  --set-env-vars "OPENAI_API_KEY=sk-proj-..."
```

### n8n Integration

The workflow connects a chat trigger to the Cloud Run endpoint and formats responses:

1. **Chat Trigger** — Captures user input
2. **HTTP Request** — Calls `POST /v1/chat-ga4` on Cloud Run
3. **Basic LLM Chain** — Humanizes the response using GPT-4o-mini
4. **Respond to Webhook** — Sends the answer back to the user

Import the workflow by uploading `n8n-workflow.json` into your n8n instance (Workflows → Add Workflow → Import from File).

## API Reference

### `POST /v1/chat-ga4`

**Request:**
```json
{
  "question": "How many unique users in January 2021?"
}
```

**Response:**
```json
{
  "status": "Success",
  "generated_sql": "SELECT COUNT(DISTINCT user_pseudo_id) AS unique_users FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` WHERE _TABLE_SUFFIX BETWEEN '20210101' AND '20210131'",
  "data": [
    { "unique_users": 12345 }
  ],
  "error": ""
}
```

## Author

**João Pedro Caldas** — [GitHub](https://github.com/jp-caldas)