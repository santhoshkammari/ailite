# ailite/model/main.py
from typing import Optional, Dict, List
from litegen.model._oai import OmniLLMClient
from litegen.model._types import ModelType

__client = None


def get_client(gpu=False):
    global __client
    if __client is None:
        __client = OmniLLMClient(gpu=gpu)
    return __client


def lazy_completion(
    model: ModelType,
    messages: Optional[List[Dict[str, str]]] | str = None,
    system_prompt: str = "You are helpful Assistant",
    prompt: str = "",
    context: Optional[List[Dict[str, str]]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    stop: Optional[List[str]] = None,
    tools=None,
    **kwargs
):
    client = get_client(kwargs.pop('gpu',False))
    return client.completion(
        model=model,
        messages=messages,
        system_prompt=system_prompt,
        prompt=prompt,
        context=context,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
        stop=stop,
        tools=tools,
        **kwargs
    )



def print_stream_completion(
    model: ModelType,
    messages: Optional[List[Dict[str, str]]] | str = None,
    system_prompt: str = "You are helpful Assistant",
    prompt: str = "",
    context: Optional[List[Dict[str, str]]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    stop: Optional[List[str]] = None,
    tools=None,
    **kwargs
):
    client = get_client(kwargs.pop('gpu',False))
    res = client.completion(
        model=model,
        messages=messages,
        system_prompt=system_prompt,
        prompt=prompt,
        context=context,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
        stop=stop,
        tools=tools,
        **kwargs
    )
    for x in res:
        print(x.choices[0].delta.content, end="", flush=True)
