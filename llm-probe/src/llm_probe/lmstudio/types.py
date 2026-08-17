"""Pydantic types for LM Studio REST API."""

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float = 0.2
    max_tokens: int = -1  # unlimited
    stream: bool = False


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Choice(BaseModel):
    message: Message
    finish_reason: str = ""


class ChatResponse(BaseModel):
    id: str = ""
    model: str = ""
    choices: list[Choice]
    usage: UsageInfo = Field(default_factory=UsageInfo)

    @property
    def content(self) -> str:
        if not self.choices:
            return ""
        return self.choices[0].message.content


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    # LM Studio может отдавать доп. поля — игнорируем
    model_config = {"extra": "ignore"}


class ModelsResponse(BaseModel):
    data: list[ModelInfo]
    model_config = {"extra": "ignore"}
