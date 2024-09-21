"""websocket関連のビジネスロジックを記載したサービスクラスを含むモジュール"""

import logging
import random
from typing import Dict
from pydantic import ValidationError
from utils.enum import MessageType, LLMType
from schema.message import (
    BaseMessage,
    ChatMessage,
    ResponseChatMessage,
    InitializeMessage,
    AnswerMessage,
    ResultMessage,
)
from domain.agent import AgentFactory, LLMAgent
from core.connection import Connection

logger = logging.getLogger(__name__)

# TODO: 今は固定でルームIDを指定
room_id = "YRHJE7tCpDtKzMnJNw3Fk48KVia4kzKU"


class WebsocketService:
    """websocket関連のビジネスロジックを記載したサービスクラス"""

    def __init__(self, agent_factory: AgentFactory) -> None:
        """websocketのサービスクラスの初期化

        :param agent_factory AI Agentを生成するファクトリー
        """
        self.agent_factory: AgentFactory = agent_factory
        self.agents: Dict[str, LLMAgent] = {}

    async def handle_message(self, message: str, connection: Connection) -> None:
        """message毎に処理の振り分けをハンドリング.json形式で返却する

        :param message websocket経由で取得したmessage
        :param websocketのコネクションの管理クラス
        :raises ValidationError messageが特定のフォーマットに沿わなかったときのエラー
        :raises NotImplementedError 要求されたAgentが現在の実装に存在しないときのエラー
        :raises Exception その他エラー
        """
        logger.info("handle massage start...")
        try:
            base_message = BaseMessage.model_validate_json(message)
            logger.info("message type is :%s", base_message.message_type)
            # TODO: ここは、色々悩みあり。
            # 1.roomごとに初期化して、別のゲームルームには知識を共有しないようにしないといけないはず。
            # 2.利用するLLMの切り分けをどうするか。設定ファイルに書くか。クライアントからもらうか。
            match base_message.message_type:
                case MessageType.INITIALIZATION:
                    initialization_message = InitializeMessage.model_validate_json(
                        message
                    )
                    if room_id not in self.agents:
                        self.agents[room_id] = self.agent_factory.create_agent(
                            initialization_message.game_type, LLMType.OLLAMA
                        )
                        logger.info(
                            "agent is generated game :%s, model : %s ",
                            initialization_message.game_type,
                            LLMType.OLLAMA.value,
                        )
                    response_message = self.agents[room_id].initialize_theme(
                        "Let's start the game!",
                    )
                    res = ResponseChatMessage(
                        message_type=MessageType.INITIALIZATION.value,
                        message=response_message,
                        sender="bot",
                    )
                    logger.info("response is :%s", res.model_dump_json())
                    await connection.broadcast(f"{res.model_dump_json()}")
                case MessageType.CHAT:
                    chat_message = ChatMessage.model_validate_json(message)
                    # TODO: Agentが存在しない場合の処理を追加する
                    response_message = self.agents[room_id].get_response(
                        chat_message.message
                    )
                    res = ResponseChatMessage(
                        message_type=MessageType.CHAT.value,
                        message=response_message,
                        sender="bot",
                    )
                    logger.info("response is :%s", res.model_dump_json())
                    await connection.broadcast(f"{res.model_dump_json()}")
                case MessageType.ANSWER:
                    chat_message = AnswerMessage.model_validate_json(message)
                    # TODO: 正誤の判定方法については、まだ明確に仕様が決まっていないため、ランダムな値を返している。
                    # blockchainから取得する予定。
                    # LLMでやるのであれば、分類専用のAgentを間に挟んで、trueかfalseしか正確に返さないような調整をすればできそう
                    result = "success" if random.randint(0, 1) == 1 else "failed"
                    res = ResultMessage(
                        message_type=MessageType.RESULT.value,
                        result=result,
                        sender="bot",
                    )
                    logger.info("response is :%s", res.model_dump_json())
                    # TODO: 本来は、ユーザーごとに結果(勝ち負け)が異なるため、broadcastはしない
                    await connection.broadcast(f"{res.model_dump_json()}")
                    # TODO: ゲームを終了したら、Agentを破棄したほうがいい
                case _:
                    logger.error(
                        "not supported message type :%s", base_message.message_type
                    )
        except ValidationError as e:
            logger.error("Error processing message:%s", e)
        except NotImplementedError as e:
            logger.error("Error processing message:%s", e)
        except Exception as e:
            logger.error("Error processing message:%s", e)
