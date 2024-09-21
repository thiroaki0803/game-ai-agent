"""websocket関連のビジネスロジックを記載したサービスクラスを含むモジュール"""

import logging
import random
from typing import Dict
from pydantic import ValidationError
from utils.enum import MessageType, LLMType
from utils import subprocess
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

# minaのワーカークラスで、処理を実行するための実行エイリアス
MINA_DEPLOY_ALIAS = "zkbot"


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
                    # TODO: 正解データをAIで数値に直す
                    # 今はコントラクトのソースコードに固定で"2"を正解としてアップデートをかけている
                    # correct_number = 2
                    # result = subprocess.execute(
                    #     "node",
                    #     "libs/contracts/build/src/interact.js",
                    #     str(correct_number),
                    # )
                    # 遅いし、毎回実行する必要なし。
                    # result = subprocess.execute(
                    #     "node",
                    #     "libs/contracts/build/src/interact.js",
                    #     MINA_DEPLOY_ALIAS,
                    # )
                    # logger.info("return code: %s", result.returncode)
                    # logger.info("Successfully set the correct number.")
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
                    # NOTE: 回答は、クライアント側で証明を生成し、検証まで呼んでもらう
                    # blockchainから取得する予定。
                    # LLMでやるのであれば、分類専用のAgentを間に挟んで、trueかfalseしか正確に返さないような調整をすればできそう
                    # result = "success" if random.randint(0, 1) == 1 else "failed"
                    # result = subprocess.execute(
                    #     "node",
                    #     "libs/contracts/build/src/verify.js",
                    #     chat_message.message,
                    # )
                    output = subprocess.execute(
                        "node",
                        "libs/contracts/build/src/verify.js",
                        MINA_DEPLOY_ALIAS,
                        chat_message.message,
                    )
                    # 出力行の最後に結果を出力している
                    lines = output.stdout.strip().splitlines()
                    result = None
                    if lines:
                        result = lines[-1]
                    res = ResultMessage(
                        message_type=MessageType.RESULT.value,
                        result="success" if result == "true" else "failed",
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
            logger.error("Error processing message validation error:%s", e)
        except NotImplementedError as e:
            logger.error("Error processing message not implemented error:%s", e)
        except Exception as e:
            logger.error("Error processing message error:%s", e)
