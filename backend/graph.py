from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langchain.schema import AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row


# ===============================================================================
# ---- PostgreSQL Connection ----

DB_URI = "postgresql://postgres:mypost@localhost:5432/langgraph_memory?sslmode=disable"

# Global variables
checkpointer = None
graph = None

async def setup_checkpointer():
    """Initialize the async PostgreSQL checkpointer"""
    
    global checkpointer
    
    # Use psycopg AsyncConnection, not asyncpg
    conn = await AsyncConnection.connect(
        DB_URI,
        autocommit=True,
        row_factory=dict_row
    )
    checkpointer = AsyncPostgresSaver(conn)

    await checkpointer.setup()
    return checkpointer

async def get_graph():
    """Get or initialize the compiled graph with checkpointer"""
    
    global checkpointer, graph
    
    if graph is None:
        checkpointer = await setup_checkpointer()
        graph = workflow.compile(checkpointer=checkpointer)  # your workflow
    
    return graph    


# ===============================================================================
# Initialize OpenAI and Pinecone clients

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

# Define retriever tool
def retriever_tool(query: str):
    # print("Retrieving documents for query...")

    """Retrieve relevant documents from Pinecone index based on the query."""
    
    print("Retriever_tool called Now Retrieving documents for query...")
    print("Query:", query)
    
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

    # Format results
    return [
        {
            "url": match["metadata"]["url"],
            "snippet": match["metadata"]["text"][:200] + "..."
        } for match in results["matches"]
    ]

# ===============================================================================
# Define the response model and generate_query_or_respond

response_model = init_chat_model("openai:gpt-4.1", temperature=0, streaming=True)

def generate_query_or_respond(state: MessagesState):
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply respond to the user.
    """

    print("generate_query_or_respond called")

        # Force the model to always include source link if available
    instruction_msg = {
        "role": "system", 
        "content": (
            "For news (global affairs, international relations, international affairs), intercurrent events, or time-sensitive information, ALWAYS use tools to get the latest data and article link."
            "Format sources as: Source: [working_link]"
        )
    }

    # Insert this instruction at the start
    messages = [instruction_msg] + state["messages"]
    
    response = (
        response_model
        .bind_tools([retriever_tool]).invoke(state["messages"])
    )
    # print(response.content)
    return {"messages": [response]}


# ==============================================================================
# Grading documents for relevance
GRADE_PROMPT = (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. Only respond with 'yes' or 'no', nothing else."
)

grader_model = init_chat_model("openai:gpt-4.1", temperature=0, streaming=False)

def grade_documents(state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
    """Determine whether the retrieved documents are relevant to the question."""
    
    print("grade_documents called")
    
    question = state["messages"][-2].content
    context = state["messages"][-1].content
    

    prompt = GRADE_PROMPT.format(question=question, context=context)
    
    response = grader_model.invoke([{"role": "user", "content": prompt}])
    print("Grader response:", response.content)

    # score = response.binary_score

    response_text = response.content.lower().strip()
    if "yes" in response_text:
        score = "yes"
    else:
        score = "no"

    if score == "yes":
        return "generate_answer"
    else:
        return "rewrite_question"
    
# ==========================================================================
# Rewrite the question to improve semantic intent
REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)


def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    
    messages = state["messages"]
    question = messages[-2].content

    print("Rewriting question...", question)
    
    prompt = REWRITE_PROMPT.format(question=question)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    
    return {"messages": [AIMessage(content=response.content)]}   

# ==========================================================================
# Generate the final answer based on the retrieved documents
GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Give answer in five sentences and keep the answer concise. For more details give the Reuters article link from context\n"
    "Question: {question} \n"
    "Context: {context}"
)


def generate_answer(state: MessagesState):
    """Generate an answer."""
    
    print("generate_answer called")

    question = state["messages"][-2].content
    context = state["messages"][-1].content
    
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    
    response = response_model.invoke([{"role": "user", "content": prompt}])
    
    return {"messages": [response]}


# ==========================================================================
# Define the workflow
workflow = StateGraph(MessagesState)

# Define the nodes we will cycle between
workflow.add_node(generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node(rewrite_question)
workflow.add_node(generate_answer)

workflow.add_edge(START, "generate_query_or_respond")

# Decide whether to retrieve
workflow.add_conditional_edges(
    "generate_query_or_respond",
    
    # Assess LLM decision (call `retriever_tool` tool or respond to the user)
    tools_condition,
    {
        # Translate the condition outputs to nodes in our graph
        "tools": "retrieve",
        END: END,
    },
)

# Edges taken after the `action` node is called.
workflow.add_conditional_edges(
    "retrieve",
    # Assess agent decision
    grade_documents,
)
workflow.add_edge("generate_answer", END)
workflow.add_edge("rewrite_question", "generate_query_or_respond")

# ==========================================================================

def count_tokens(messages):
    """Count tokens in messages using OpenAI's chat model."""
    
    print("count_tokens called")
    try:
        # Convert to OpenAI format
        openai_messages = []
        for msg in messages:
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, 'type', 'unknown')
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, 'content', '')
            
            # Convert LangChain roles to OpenAI roles
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            elif role == "tool":
                # Skip tool messages or convert to user message for token counting
                role = "user"
                content = f"Tool result: {content}" 
            
            # Only add messages with valid content
            if content and role in ["user", "assistant", "system"]:
                openai_messages.append({"role": role, "content": str(content)})

        # Use OpenAI's chat completion to get token count
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            max_tokens=1,  # only want the token count, not the response
            stream=False
        )
        return response.usage.prompt_tokens
    except Exception as e:
        print(f"Error counting tokens: {e}")


def trim_messages(messages, max_tokens):
    """Trim messages to stay within token limit while preserving conversation flow."""
    
    if not messages:
        print("No messages are available to trim.")
        return messages
    
    # Always keep the first message (original user query) and last few messages
    if len(messages) <= 2:
        print("Messages lengths are short, no trimming needed.")
        return messages
    
    # Check if current messages exceed token limit
    current_tokens = count_tokens(messages)
    
    if current_tokens <= max_tokens:
        print(f"Current token count ({current_tokens}) is within the limit ({max_tokens}). No trimming needed.")
        return messages
    
    print(f"Token limit exceeded ({current_tokens} > {max_tokens}). Trimming messages...")
    
    # Strategy: Keep first message, system message last 2-3 messages, and trim middle
    system_msgs = [msg for msg in messages if (msg.get("role") if isinstance(msg, dict) else getattr(msg, 'type', None)) == "system"]
    first_msg = messages[1]  # Original user query
    last_msgs = messages[-2:]  # Recent conversation
    
    # Start with essential messages
    trimmed = system_msgs + [first_msg] + last_msgs
    
    # Add messages from the end working backwards until we hit token limit ()
    # Preserve [Some middle] messages
    for msg in reversed(messages[1:-2]):
        test_messages = [first_msg, msg] + last_msgs
        if count_tokens(test_messages) <= max_tokens:
            trimmed.insert(-2, msg)  # Insert before last_msgs
        else:
            break
    
    final_tokens = count_tokens(trimmed)
    print(f"Trimmed to {len(trimmed)} messages ({final_tokens} tokens)")
    
    return trimmed 
# ==========================================================================

async def run_workflow(query: str, thread_id: str, max_tokens):
    """Run the workflow with the given query."""

    # Get the initialized graph
    graph = await get_graph()

    print("run_workflow called with thread_id:", thread_id)
    
    # Fetch the full conversation before starting
    existing_messages = await get_full_conversation(thread_id)  
    
    # Add system message if conversation is new
    if not existing_messages:
        sys_msg = {"role": "system", "content": "You are a helpful AI assistant. Never use your context for news always use tools for news (global affairs, international relations, international affairs) to get the data and article link."
            "Format sources as: Source: [link]"        
            "If you don't know the answer, just say I don't know."
        ""}
        
        existing_messages = [sys_msg]
    
    new_message = {"role": "user", "content": query}
    all_messages = existing_messages + [new_message]

    # Final trim including new message
    all_messages = trim_messages(all_messages, max_tokens)
    
    print(f"Running workflow with {len(all_messages)} messages...")
    # print_trimmed_messages(all_messages)

    config = {"configurable": {"thread_id": thread_id}}
    
    # return graph.astream({"messages": all_messages}, config)
    return graph.astream_events({"messages": all_messages}, config, version="v1")
    

def print_trimmed_messages(messages):
    for i, msg in enumerate(messages, 1):
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, 'type', 'unknown')
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, 'content', '')
        print(f"[{i}] {role.upper()}: {content}")

async def get_full_conversation(thread_id: str):
    """Retrieve all messages from the conversation."""

     # Get the checkpointer from the initialized graph
    global checkpointer
    if checkpointer is None:
        # Initialize if not done yet
        await get_graph()


    # Load the latest state from Postgres
    config = {"configurable": {"thread_id": thread_id}}  
    state_tuple = await checkpointer.aget_tuple(config)
    
    if not state_tuple or not state_tuple.checkpoint.get("channel_values", {}).get("messages"):
        return []
    
    
    channel_values = state_tuple.checkpoint.get("channel_values", {})
    messages = channel_values.get("messages", [])
        
    return messages



async def show_full_conversation(thread_id: str):
    """Display the full conversation for a given thread."""
    
    messages = await get_full_conversation(thread_id)
    if not messages:
        print("No conversation found for this thread.")
        return
    
    print(f"\n--- Full Conversation (Thread: {thread_id}) ---\n")
    for i, msg in enumerate(messages, 1):
        print(f"[{i}] {msg.type.upper()}: {msg.content}")
        print("-" * 50)   



# ==============================================================================
import asyncio

async def get_all_thread_ids(user_id: str):
   """Get all thread IDs with their first message as title (latest checkpoints only)."""
   
   print("get_all_thread_ids called")
   
   try:
       global checkpointer
       if checkpointer is None:
           await get_graph()
       
       thread_data = []
       seen_threads = set()
       print("Starting checkpointer.alist...")
       
       # Add timeout to prevent hanging
       try:
           # Use asyncio.wait_for instead of asyncio.timeout for compatibility
           async def get_checkpoints():
               checkpoint_list = []
               
               async for checkpoint_tuple in checkpointer.alist({}):
                   checkpoint_list.append(checkpoint_tuple)
               return checkpoint_list
           
           checkpoints = await asyncio.wait_for(get_checkpoints(), timeout=15.0)
           print(f"Retrieved {len(checkpoints)} checkpoints")
           
           for checkpoint_tuple in checkpoints:
               thread_id = checkpoint_tuple.config.get("configurable", {}).get("thread_id")
               

               # Only include threads that belong to this user
               if thread_id and thread_id.startswith(f"{user_id}_"):
                  
                   # Skip if we already processed this thread_id
                   if thread_id and thread_id not in seen_threads:
                       seen_threads.add(thread_id)
                       
                       # Get LATEST state for this thread_id (same as get_full_conversation)
                       config = {"configurable": {"thread_id": thread_id}}  
                       state_tuple = await checkpointer.aget_tuple(config)
                       
                       if state_tuple:
                           channel_values = state_tuple.checkpoint.get("channel_values", {})
                           messages = channel_values.get("messages", [])
                           
                           # Get first human message as title
                           title = "New Chat"
                           for msg in messages:
                               try:
                                   if hasattr(msg, 'type') and hasattr(msg, 'content'):
                                       if msg.type == "human" and msg.content:
                                           content = msg.content
                                           title = content[:30] + "..." if len(content) > 30 else content
                                           break
                                   elif isinstance(msg, dict) and msg.get("type") == "human":
                                       if msg.get("content"):
                                           content = msg["content"]
                                           title = content[:30] + "..." if len(content) > 30 else content
                                           break
                               except Exception as msg_error:
                                   print(f"Error processing message: {msg_error}")
                                   continue
                           
                           thread_data.append({
                               "thread_id": thread_id,
                               "title": title
                           })
                           
       except asyncio.TimeoutError:
           print("Timeout waiting for checkpointer.alist() - returning partial results")
       except Exception as list_error:
           print(f"Error in checkpointer.alist(): {list_error}")
           return []
       
            
       print(f"Found {len(thread_data)} unique threads.")
       return thread_data
       
   except Exception as e:
       print(f"Error getting thread IDs: {e}")
       import traceback
       traceback.print_exc()
       return []
# ==========================================================================

if __name__ == "__main__":

    thread_id = "session_6"

    query = "African Development Bank loan to South Africa for energy and rail infrastructure improvements"
    
    run_workflow(query, thread_id, 128000)      
    
    # Print the full conversation
    show_full_conversation(thread_id)