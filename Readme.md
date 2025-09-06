# Global Affairs Agentic RAG System

An AI-powered chat platform for global affairs and international relations. It uses FastAPI for the backend, LangChain/LangGraph for conversational workflows, OpenAI for language modeling, Pinecone for document retrieval, and PostgreSQL for persistent chat history. It scrapes recent news articles from Reuters using Scraper API and newspaper3k.

## Features

- Real-time chat via WebSocket
- Streaming responses for a smoother chat experience
- Source URLs included in agent responses
- Message trimming to avoid exceeding token limits
- News/document retrieval using Pinecone and OpenAI embeddings
- Scrape news articles from Reuters
- Persistent conversation history (PostgreSQL)
- Semantic search, query rewriting, and relevance grading
- Static frontend
- Schema-Service-Controller (SSC) Design Pattern
- Vertical Slicing

## Technologies

- FastAPI
- LangChain & LangGraph
- OpenAI API
- Pinecone
- PostgreSQL (async)
- Pydantic
- WebSocket
- Scraper API and newspaper3k

## Project Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── slices/
│   │   │   ├── auth/
│   │   │   ├── chats/
│   │   │   └── realtime/
│   │   └── server.py
│   ├── graph.py
│   ├── main.py
├── frontend/
│   ├── index.html
│   ├── myscript.js
│   └── style.css
├── .gitignore
├── requirements.txt
├── global-affairs-rag-firebase-adminsdk.json
├── myenv/ (virtual environment)
└── Readme.md
```

## Getting Started

### Backend Setup

1. Activate the virtual environment:
   ```powershell
   .\myenv\Scripts\Activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file with your OpenAI, Pinecone, and other API keys.
4. Run the backend server:
   ```powershell
   uvicorn backend.main:app --reload
   ```

### Frontend
- Static files: `index.html`, `myscript.js`, `style.css`
- Place your frontend code in the `frontend/` folder
- Open your browser at [http://localhost:8000]

## Environment & Data
- `.env` for secrets (not committed)
- Firebase credentials: `backend/global-affairs-rag-firebase-adminsdk.json` (ignored by git)
- `reuters_articles.json` for data processing (ignored by git if not needed)

## API Endpoints (examples)

- `GET /` — Home page
- `GET /chats/{user_id}` — List chat threads for a user
- `GET /chat/{thread_id}` — Retrieve chat history for a thread
- `WS /ws/{thread_id}/{user_id}` — WebSocket for real-time chat

## Best Practices
- Exclude `myenv/`, `__pycache__/`, and other generated files from git (see `.gitignore`)
- Add a `tests/` folder for backend tests as your project grows
- Keep credentials and sensitive data out of version control


## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [OpenAI](https://openai.com/)
- [Pinecone](https://www.pinecone.io/)
- [FastAPI](https://fastapi.tiangolo.com/)


👨‍💻 Author: Muhammad Muaaz
