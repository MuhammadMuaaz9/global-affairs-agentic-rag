import json
import uuid
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

# --- Initialize clients ---
client =  OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create Pinecone index if it doesn't exist
if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    print(f"Creating index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,  # for text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(INDEX_NAME)

# --- Load JSON articles ---
with open("reuters_articles.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

# --- Split into chunks ---
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
all_chunks = []

for article in articles:
    chunks = splitter.split_text(article["full_text"])
    for chunk in chunks:
        all_chunks.append({
            "id": str(uuid.uuid4()),
            "text": chunk,
            "metadata": {
                "title": article["title"],
                "publication_date": article["publication_date"],
                "url": article["url"]
            }
        })

print(f"Total chunks to embed: {len(all_chunks)}")

# --- Create embeddings in batches ---
BATCH_SIZE = 100
for i in range(0, len(all_chunks), BATCH_SIZE):
    batch = all_chunks[i:i + BATCH_SIZE]

    # Extract only text for embedding
    texts = [item["text"] for item in batch]

    # Call OpenAI embedding API once for the whole batch
    emb_response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    # Prepare Pinecone vectors
    vectors = []
    for j, emb_data in enumerate(emb_response.data):
        vectors.append({
            "id": batch[j]["id"],
            "values": emb_data.embedding,
            "metadata": {
                **batch[j]["metadata"],
                "text": batch[j]["text"]
            }
        })

    # Upload to Pinecone
    index.upsert(vectors=vectors)
    print(f"Uploaded batch {i // BATCH_SIZE + 1}")

print("All embeddings uploaded successfully!")