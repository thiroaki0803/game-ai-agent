from pydantic import BaseModel, Field
from utils.enum import MessageType, GameType


class BaseMessage(BaseModel):
    message_type: MessageType = Field(..., description="メッセージタイプ")


class ChatMessage(BaseMessage):
    message: str = Field(..., description="メッセージ本文")
    sender: str = Field(..., description="送信者")


class ResponseChatMessage(BaseMessage):
    message_type: str = Field(..., description="Unity返却用のメッセージタイプ")
    message: str = Field(..., description="メッセージ本文")
    sender: str = Field(..., description="送信者名")


class InitializeMessage(BaseMessage):
    # roomId: str = Field(..., description="どのゲームのルームに対してか") #まだ不要
    game_type: GameType = Field(..., description="何のゲームを開始するか")
    sender: str = Field(..., description="送信者名")
