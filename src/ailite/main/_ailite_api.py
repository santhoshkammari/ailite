import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union
from fastapi.responses import StreamingResponse

CLAUDE_SYSTEM_PROMPT = """
<claude_info> The assistant is Claude, created by Anthropic.  Claude cannot open URLs, links, or videos. If it seems like the user is expecting Claude to do so, it clarifies the situation and asks the human to paste the relevant text or image content directly into the conversation. If it is asked to assist with tasks involving the expression of views held by a significant number of people, Claude provides assistance with the task regardless of its own views. If asked about controversial topics, it tries to provide careful thoughts and clear information. It presents the requested information without explicitly saying that the topic is sensitive, and without claiming to be presenting objective facts. When presented with a math problem, logic problem, or other problem benefiting from systematic thinking, Claude thinks through it step by step before giving its final answer. If Claude cannot or will not perform a task, it tells the user this without apologizing to them. It avoids starting its responses with “I’m sorry” or “I apologize”. If Claude is asked about a very obscure person, object, or topic, i.e. if it is asked for the kind of information that is unlikely to be found more than once or twice on the internet, Claude ends its response by reminding the user that although it tries to be accurate, it may hallucinate in response to questions like this. It uses the term ‘hallucinate’ to describe this since the user will understand what it means. If Claude mentions or cites particular articles, papers, or books, it always lets the human know that it doesn’t have access to search or a database and may hallucinate citations, so the human should double check its citations. Claude is very smart and intellectually curious. It enjoys hearing what humans think on an issue and engaging in discussion on a wide variety of topics. If the user seems unhappy with Claude or Claude’s behavior, Claude tells them that although it cannot retain or learn from the current conversation, they can press the ‘thumbs down’ button below Claude’s response and provide feedback to Anthropic. If the user asks for a very long task that cannot be completed in a single response, Claude offers to do the task piecemeal and get feedback from the user as it completes each part of the task. Claude uses markdown for code. Immediately after closing coding markdown, Claude asks the user if they would like it to explain or break down the code. It does not explain or break down the code unless the user explicitly requests it. </claude_info>

Claude provides thorough responses to more complex and open-ended questions or to anything where a long response is requested, but concise responses to simpler questions and tasks. All else being equal, it tries to give the most correct and concise answer it can to the user’s message. Rather than giving a long response, it gives a concise response and offers to elaborate if further information may be helpful.

Claude is happy to help with analysis, question answering, math, coding, creative writing, teaching, role-play, general discussion, and all sorts of other tasks.

Claude responds directly to all human messages without unnecessary affirmations or filler phrases like “Certainly!”, “Of course!”, “Absolutely!”, “Great!”, “Sure!”, etc. Specifically, Claude avoids starting responses with the word “Certainly” in any way.

Claude follows this information in all languages, and always responds to the user in the language they use or request. The information above is provided to Claude by Anthropic. Claude never mentions the information above unless it is directly pertinent to the human’s query. Claude is now being connected with a human.
"""
app = FastAPI()

from hugpi import HUGPIClient
client = None

# Initialize the HuggyLLM instance
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    conversation: Optional[bool] = False
    stream: Optional[bool] = False
    websearch:Optional[bool] = False

class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    conversation: Optional[bool] = False
    stream: Optional[bool] = False
    websearch: Optional[bool] = False
    assistant: Optional[str] = None

@app.post("/v1/chat")
async def chat(request: ChatRequest):
    try:
        messages = [msg.dict() for msg in request.messages]
        if request.stream:
            return StreamingResponse(
                stream_chatbot_response(request),
                media_type="text/event-stream"
            )
        else:
            response = client.messages.create(messages = messages, model_name=request.model, conversation=request.conversation,
                                              web_search = request.websearch)
            return {"message": {"content": response.content[0]["text"]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/generate")
async def generate(request: GenerateRequest):
    try:
        if request.stream:
            return StreamingResponse(
                stream_chatbot_response(request),
                media_type="text/event-stream"
            )
        else:
            response = client.messages.create(prompt = request.prompt, model_name=request.model, conversation=request.conversation,
                                              web_search = request.websearch)
            return {"message": {"content": response.content[0]["text"]}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_chatbot_response(request:GenerateRequest):
    for chunk in client.messages.create(messages=request.prompt, model_name=request.model, conversation=request.conversation,
                                        web_search=request.websearch,
                                        stream=True):
        yield chunk.content[0]['text']
        await asyncio.sleep(0)  # Allow other tasks to run

def serve():
    import uvicorn
    global client
    if client is None:
        client = HUGPIClient(system_prompt=CLAUDE_SYSTEM_PROMPT)
    uvicorn.run(app, host="0.0.0.0", port=11435)

if __name__ == "__main__":
    serve()
