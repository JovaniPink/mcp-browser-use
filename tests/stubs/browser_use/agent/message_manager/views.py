from dataclasses import dataclass, field
from typing import Any, List

@dataclass
class MessageHistory:
    messages: List[Any] = field(default_factory=list)
    total_tokens: int = 0

@dataclass
class ManagedMessage:
    message: Any
