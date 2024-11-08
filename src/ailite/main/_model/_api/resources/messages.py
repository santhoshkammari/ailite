import uuid
import json
import re
from typing import Union, Dict, List, Generator, Iterable, Callable, Optional

from langchain_core.utils import print_text

from .._models import HUGPiLLM
from .._tool_calling import ToolPrepare
from ..types._message import Message
from ..types._model_types import MODELS_TYPE
from ..types.tool_param import ToolParam
from ..types.usage import Usage
import logging

from ..._utils._const import AVAILABLE_MODEL_LIST

logger = logging.getLogger(__name__)
logger.setLevel(level='DEBUG')



class Messages:
    def __init__(self, llm):
        self.llm:HUGPiLLM = llm
        self.system_prompt = ""
        self.tools = None



    def create(
            self,
            model: Union[MODELS_TYPE, None] = 'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF',
            prompt: str | None = None,
            messages: List[Dict[str, Union[str, int, float]]] | None = None,
            tools: Iterable[ToolParam] | None = None,
            tool_prompt:str| None = None,
            tool_schema_func: Callable | None= None,
            tool_parse_func: Callable | None= None,
            tool_execute_func: Callable | None= None,
            stream: bool = False,
            conversation: bool = False,
            max_tokens: int | None = None,
            assistant:Optional[str] = None,
        **kwargs
    ) -> Message | Generator:
        self.tool_parse_func = tool_parse_func
        self.tool_execute_func = tool_execute_func
        if tools:
            self.tools = tools
            self.tool_prompt = ToolPrepare._transformers_prepare_tool_prompt(tools,
                                                                             tool_prompt = tool_prompt,
                                                                             tool_schema_func=tool_schema_func)
        if kwargs.get("debug",False):
            print(f"System Prompt: {self.system_prompt}")
            print(f"User Prompt: {prompt or messages}")
            print(f"Tools: {self.tools}")
            print(f"Max Tokens: {max_tokens}")
            print(f"Model: {model}")
            print(f"Stream: {stream}")
            print(f"Conversation: {conversation}")
            print(f"kwargs: {kwargs}")

        if stream:
            return self.stream(model=model, messages=prompt or messages, conversation=conversation,
                               max_tokens=max_tokens, assistant=assistant,**kwargs)
        else:
            return self.invoke(model=model, messages=messages or prompt, conversation=conversation,
                               max_tokens=max_tokens, assistant=assistant,**kwargs)

    def _get_sys_and_user_prompt(self, messages: Union[List[Dict], str]):
        if isinstance(messages, str):
            return self.system_prompt+self.tool_prompt if self.tools else "", messages
        sp, up = self.system_prompt+self.tool_prompt if self.tools else "", ""
        for m in messages:
            if m['role'] == "system":
                sp += m['content']
            elif m['role'] == "user":
                up = m['content']
        return sp, up

    def _parse_tool_use(self, content: str) -> Dict[str, Union[str, Dict]]:
        if 'tool_call' in content:
            start,end = 0,len(content)
            start_flag = True
            for idx,ch in enumerate(content):
                if ch=='{' and start_flag:
                    start=idx
                    start_flag=False
                if ch=="}":
                    end = idx+1
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                return {}

    def _execute_tool(self, tool_call: Dict[str, Union[str, Dict]]) -> str:
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        result = None
        for tool in self.tools:
            if callable(tool) and tool.__name__ == tool_name:
                try:
                    result = tool(**arguments)
                except Exception as e:
                    result = f"Error {e} for {tool_name} with args: {arguments}"
        return result

    def invoke(self, messages: Union[List, str], model: str = None,
               max_tokens: int | None = None,
               conversation: Union[bool, None] = None,
               assistant: Optional[str] = None,
               **kwargs):
        response: str = ""
        for value in self.stream(model=model,messages=messages,
                             conversation=conversation,max_tokens=max_tokens,
            assistant=assistant,
                             **kwargs):
            response += value.content[0]["text"]

        if kwargs.get("debug", False):
            print('########################')
            print("### Invoke Response ###")
            print(response)
            print('########################')

        tool_call = self._parse_tool_use(response) if self.tool_parse_func is None else self.tool_parse_func(response)

        if kwargs.get("debug", False):
            print("### tool_call Parsed ###")
            print(json.dumps(tool_call, indent=4))
            print('################')

        usage = Usage(input_tokens=10, output_tokens=10)

        if tool_call:
            results = self._execute_tool(tool_call) if self.tool_execute_func is None else self.tool_execute_func(tool_call)
            if results and tool_call.get("name") and tool_call.get("arguments"):
                return  Message(
                    id=str(uuid.uuid4()),
                    role="assistant",
                    content=[
                        {
                            "type": "tool_result",
                            "tool_use_id": f"tool_{str(uuid.uuid4())}",
                            "content":results
                        }
                    ],
                    type='message',
                    model=model if model else 'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF',
                    conversation=conversation,
                    usage = usage,
                    **kwargs
                )
            else:
                return Message(
                    id=str(uuid.uuid4()),
                    role="assistant",
                    content=[
                        {
                            "type": "tool_use",
                            "id": f"tool_{str(uuid.uuid4)}",
                            "name":tool_call.get("name",""),
                            "input":tool_call.get("arguments",{})
                        }
                    ],
                    type='message',
                    model=model if model else 'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF',
                    conversation=conversation,
                    usage=usage,
                    **kwargs
                )
        else:
            return  Message(
                id=str(uuid.uuid4()),
                role="assistant",
                content=[
                    {
                        "type": "text",
                        "text": response
                    }
                ],
                type='message',
                model=model if model else 'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF',
                conversation=conversation,
                usage=usage,

                **kwargs
            )

    def stream(
            self,
            messages: Union[List, str],
            model: str = None,
            max_tokens: int | None = None,
            conversation: Union[bool, None] = None,
            assistant:Union[str,None] = None,
            **kwargs):
        user_prompt = self._update_dependencies(model=model,
                                                messages=messages,
                                                conversation=conversation,
                                                assistant=assistant)
        res = self.llm.chat(user_prompt, stream=True, **kwargs)
        for token in self._stream_with_chat(res, max_tokens):
            if token == '<MAX_TOKEN_REACHED>':
                break
            usage = Usage(input_tokens=10, output_tokens=10)
            yield Message(
                id=str(uuid.uuid4()),
                role="assistant",
                content=[{"type": "text", "text": token}],
                type='message',
                model=model if model else 'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF',
                conversation=conversation,
                usage=usage,
                **kwargs
            )



    def _update_dependencies(self, model, messages, conversation,assistant=None):
        conversation = False if conversation is None else conversation
        curr_sys_prompt, user_prompt = self._get_sys_and_user_prompt(messages)

        if assistant or (not conversation) or model!='nvidia/Llama-3.1-Nemotron-70B-Instruct-HF':
            if curr_sys_prompt and (curr_sys_prompt != self.system_prompt):
                self.system_prompt = curr_sys_prompt + self.tool_prompt if self.tools else ""
            if assistant:
                assistant = self.llm.search_assistant(assistant_name=assistant)
            self.llm.new_conversation(modelIndex=AVAILABLE_MODEL_LIST.index(model) if model else 0,
                                      system_prompt=self.system_prompt,
                                      switch_to=True,
                                      assistant=assistant)
        return user_prompt

    def _stream_with_chat(self, res, max_tokens):
        token_count = 0
        for x in res:
            if x and isinstance(x, dict):
                res = x.get('token', "")
                if max_tokens and token_count >= max_tokens:
                    yield "<MAX_TOKEN_REACHED>"
                token_count += 1
                yield res
            else:
                yield "<MAX_TOKEN_REACHED>"