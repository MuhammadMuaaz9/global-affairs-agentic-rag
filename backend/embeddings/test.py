import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Get API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "news-articles"  

# Initialize clients
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)

# Connect to existing index
index = pc.Index(INDEX_NAME)

# --- Run search ---
query = "African Development Bank loan to South Africa for energy and rail infrastructure improvements"

# Create embedding for query
query_emb = client.embeddings.create(
    model="text-embedding-3-small",
    input=query
).data[0].embedding

# Query Pinecone
results = index.query(
    vector=query_emb,
    top_k=3,
    include_metadata=True
)

# Display results
for match in results["matches"]:
    print(f"Score: {match['score']:.4f}")
    print(f"Title: {match['metadata']['title']}")
    print(f"URL: {match['metadata']['url']}")
    print(f"Snippet: {match['metadata']['text'][:200]}...\n")
