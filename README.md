# Global Affairs Agentic RAG System

An AI-powered chat platform for global affairs, international relations. It uses FastAPI for the backend, LangChain/LangGraph for conversational workflows, OpenAI for language modeling, Pinecone for document retrieval, and PostgreSQL for persistent chat history. It will scrape data/news articles of last month from the Reuters website using the Scraper api and newspaper3k.

## Features

- Real-time chat via WebSocket
- News/document retrieval using Pinecone and OpenAI embeddings
- Scrape data/news articles from the Reuters website 
- Persistent conversation history (PostgreSQL)
- Semantic search, query rewriting, and relevance grading
- Frontend served as static files

## Technologies

- FastAPI
- LangChain & LangGraph
- OpenAI API
- Pinecone
- PostgreSQL (async)
- Pydantic
- WebSocket
- Scraper api and newspaper3k

## Getting Started

1. **Clone the repository**
   ```sh
   git clone https://github.com/MuhammadMuaaz9/global-affairs-system.git
   cd global-affairs-system/backend
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Create a `.env` file in `backend/` with your OpenAI and Pinecone API keys.

4. **Start PostgreSQL**
   - Ensure PostgreSQL is running and accessible at the configured URI.

5. **Run the backend server**
   ```sh
   uvicorn main:app --reload
   ```

6. **Access the frontend**
   - Open your browser at [http://localhost:8000](http://localhost:8000).

## Project Structure

```
backend/
    web scraping/scraping.py
    web scraping/getUrls.py
    embeddings/embeddings.py
    graph.py
    main.py
frontend/
    index.html
    myscript.js
    style.css
requirements.txt    
```

## API Endpoints

- `GET /` — Home page
- `GET /chats/{user_id}` — List chat threads for a user
- `GET /chat/{thread_id}` — Retrieve chat history for a thread
- `WS /ws/{thread_id}/{user_id}` — WebSocket for real-time chat

## License

MIT License

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [OpenAI](https://openai.com/)
- [Pinecone](https://www.pinecone.io/)
- [FastAPI](https://fastapi.tiangolo.com/)

👨‍💻 Author Muhammad Muaaz
