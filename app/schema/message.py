"""websocketでやり取りするメッセージのDTO"""

from pydantic import BaseModel, Field
from utils.enum import MessageType, GameType


class BaseMessage(BaseModel):
    """すべてのメッセージの基底クラス"""

    message_type: MessageType = Field(..., description="メッセージタイプ")


class ChatMessage(BaseMessage):
    """ユーザーからのメッセージのDTO"""

    message: str = Field(..., description="メッセージ本文")
    sender: str = Field(..., description="送信者")


class ResponseChatMessage(BaseMessage):
    """APIからの送るレスポンスメッセージのDTO"""

    message_type: str = Field(..., description="Unity返却用のメッセージタイプ")
    message: str = Field(..., description="メッセージ本文")
    sender: str = Field(..., description="送信者名")


class InitializeMessage(BaseMessage):
    """システムやユーザーから、ゲームを始める際に送るメッセージのDTO"""

    # roomId: str = Field(..., description="どのゲームのルームに対してか") #まだ不要
    game_type: GameType = Field(..., description="何のゲームを開始するか")
    sender: str = Field(..., description="送信者名")


class AnswerMessage(BaseMessage):
    """ユーザーからの回答で送るメッセージのDTO"""

    message: str = Field(..., description="回答のメッセージ")
    sender: str = Field(..., description="送信者名")


class ResultMessage(BaseMessage):
    """ユーザーからの回答に対して、正誤判定を行った結果メッセージのDTO.基本的には、broadcastで送信しない"""

    message_type: str = Field(..., description="返却用のメッセージタイプ")
    result: str = Field(..., description="ゲームの結果")  # 他のゲームも考慮し、文字列型
    sender: str = Field(..., description="送信者名")
