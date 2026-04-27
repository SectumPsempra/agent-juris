from src.agents.prompts.drafting import SYSTEM_PROMPT as DRAFTING_PROMPT
from src.agents.prompts.extraction import (
    FEW_SHOT_ASSISTANT,
    FEW_SHOT_USER,
)
from src.agents.prompts.extraction import (
    PROMPT_VERSION as EXTRACTION_PROMPT_VERSION,
)
from src.agents.prompts.extraction import (
    SYSTEM_PROMPT as EXTRACTION_PROMPT,
)
from src.agents.prompts.qa import SYSTEM_PROMPT as QA_PROMPT
from src.agents.prompts.strategy import SYSTEM_PROMPT as STRATEGY_PROMPT

__all__ = [
    "EXTRACTION_PROMPT",
    "EXTRACTION_PROMPT_VERSION",
    "FEW_SHOT_USER",
    "FEW_SHOT_ASSISTANT",
    "STRATEGY_PROMPT",
    "DRAFTING_PROMPT",
    "QA_PROMPT",
]
