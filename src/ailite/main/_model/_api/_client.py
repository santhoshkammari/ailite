from .resources.messages import Messages
from ._models import HUGPiLLM
from .types._model_types import MODELS_TYPE
from .._utils._const import AVAILABLE_MODEL_LIST

class HUGPIClient:
    def __init__(
            self,
            model:MODELS_TYPE = 'nvidia/Llama-3.1-Nemotron-70B-Instruct-HF',
            api_key:str|None = 'backupsanthosh1@gmail.com_SK99@pass',
            cookie_dir_path: str = "./cookies/",
            save_cookies: bool = True,
            system_prompt:str = ""
    ):
        _hf_email,_hf_password = api_key.split("@gmail.com_")
        default_llm_index = AVAILABLE_MODEL_LIST.index(model)
        self.llm = HUGPiLLM(
            hf_email=_hf_email+'@gmail.com',
            hf_password=_hf_password,
            cookie_dir_path=cookie_dir_path,
            save_cookies=save_cookies,
            default_llm=default_llm_index,
            system_prompt=system_prompt
        )
        self.messages = Messages(self.llm)

