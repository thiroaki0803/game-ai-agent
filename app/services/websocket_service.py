"""websocket関連のビジネスロジックを記載したサービスクラスを含むモジュール"""

import logging
from typing import Dict
from pydantic import ValidationError
from utils.enum import MessageType, LLMType
from schema.message import (
    BaseMessage,
    ChatMessage,
    ResponseChatMessage,
    InitializeMessage,
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
            # 2.利用するLLMの切り分けをどうするか。設定ファイルに書くか。クライアントからもらうか。(ゲームタイプは1が実装できていればクライアントからもらう)
            match base_message.message_type:
                case MessageType.INITIALIZATION:
                    initialization_message = InitializeMessage.model_validate_json(
                        message
                    )
                    if room_id not in self.agents:
                        self.agents[room_id] = self.agent_factory.create_agent(
                            initialization_message.game_type, LLMType.OPEN_AI
                        )
                        logger.info(
                            "agent is generated game :%s, model : %s ",
                            initialization_message.game_type,
                            LLMType.OPEN_AI.value,
                        )
                    response_message = self.agents[room_id].direct(
                        "この投げかけへの「わかりました」などの受け答えは不要です。ゲームを開始してください。",
                    )
                    res = ResponseChatMessage(
                        message_type=MessageType.CHAT.value,
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
                case _:
                    logger.error(
                        "not suported message type :%s", base_message.message_type
                    )
        except ValidationError as e:
            logger.error("Error processing message:%s", e)
        except NotImplementedError as e:
            logger.error("Error processing message:%s", e)
        except Exception as e:
            logger.error("Error processing message:%s", e)
