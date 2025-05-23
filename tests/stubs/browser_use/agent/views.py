from dataclasses import dataclass, field
from typing import Any, List, Optional

@dataclass
class ActionResult:
    extracted_content: Optional[str] = None
    error: Optional[str] = None
    is_done: bool = False
    include_in_memory: bool = False

@dataclass
class AgentHistory:
    model_output: Any
    state: Any
    result: List[ActionResult]

@dataclass
class AgentHistoryList:
    history: List[AgentHistory] = field(default_factory=list)
    def is_done(self) -> bool:
        for h in self.history:
            for r in h.result:
                if r.is_done:
                    return True
        return False

@dataclass
class AgentStepInfo:
    step_number: int = 0

class AgentOutput:
    pass
