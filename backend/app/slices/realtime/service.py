from typing import AsyncIterator, Dict, Any
from ....graph import run_workflow


async def stream_chat(query: str, thread_id: str, max_tokens: int) -> AsyncIterator[Dict[str, Any]]:
    stream = await run_workflow(query, thread_id, max_tokens)
    if stream is None:
        return
    async for event in stream:
        yield event


