from enum import Enum


class MessageType(str, Enum):
    INITIALIZATION = "initialization"
    CHAT = "chat"


class GameType(str, Enum):
    TOW_TRUTH_A_LIE = "tow_truth_a_lie"


class LLMType(str, Enum):
    OPEN_AI = "openai"
    OLLAMA = "olamma"
