# Grading documents for relevance
GRADE_PROMPT = (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. Only respond with 'yes' or 'no', nothing else."
)

# Rewrite the question to improve semantic intent
REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)

# Generate the final answer based on the retrieved documents
GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Give answer in five sentences and keep the answer concise. For more details give the Reuters article link from context\n"
    "Question: {question} \n"
    "Context: {context}"
)

sys_msg = {"role": "system", "content": "You are a helpful AI assistant. Never use your context for news always use tools for news (global affairs, international relations, international affairs) to get the data and article link."
    "Format sources as: Source: [link]"        
    "If you don't know the answer, just say I don't know."
""}