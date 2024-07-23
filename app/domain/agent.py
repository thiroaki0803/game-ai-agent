"""AI Agentのドメイン管理とビジネスロジックを管理している
"""

import logging
from abc import ABC, abstractmethod
from collections import deque
from openai import OpenAI
from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from utils.enum import GameType, LLMType
from core.config import Settings


logger = logging.getLogger(__name__)


class LLMAgent(ABC):
    """LLMのAgent仮想クラス"""

    @abstractmethod
    def get_response(self, prompt: str) -> str:
        """LLMモデルに対してプロンプトを入力し、応答を取得する

        :param prompt LLMに対しての入力テキスト
        """


class OpenAIAgent(LLMAgent):
    """Open AIを使ったAI Agent

    ゲームやルームごとに生成されるAI Agent
    それぞれにシステムプロンプトや、会話履歴を持っている
    """

    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    def __init__(self, api_key: str, model_name: str, system_prompt: str) -> None:
        """OpenAIを利用した AI Agentの初期化

        :param api_key OpenAIのAPIKey
        :param model_name 利用するLLMの名称
        :param system_prompt ユーザーの役割付けをするためのシステムプロンプト
        """
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = system_prompt
        self.histories = []

    def get_response(self, prompt: str) -> str:
        """AI からの応答を取得する

        :param str prompt: ユーザーから送られたメッセージ
        """
        # TODO: できれば、RAGなどつけたい
        # ユーザーからのメッセージを履歴に追加
        # TODO: 記憶には残せるようになったが、"出題"を確実に履歴に残せるようにしなければならない
        self.histories.append({"role": self.ROLE_USER, "content": prompt})
        # 履歴のサイズを制限 (直近の10件)
        if len(self.histories) > 10:
            self.histories = self.histories[-10:]
        # システムプロンプトと履歴を含むメッセージリストを構築
        messages = [{"role": self.ROLE_SYSTEM, "content": self.system_prompt}]
        messages.extend(self.histories)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name, messages=messages
            )
            response_message = {
                "role": self.ROLE_ASSISTANT,
                "content": response.choices[0].message.content,
            }
            self.histories.append(response_message)
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        return response.choices[0].message.content


class OllamaAgent(LLMAgent):
    """ollamaを使ったAI Agent"""

    # クラス変数としてプレフィックスを定義
    SYSTEM_PREFIX = "[system]\n"
    USER_PREFIX = "[user]\n"
    ASSISTANT_PREFIX = "[assistant]\n"
    SEPARATOR = "\n\n"
    ROLE_SYSTEM = "system"
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    def __init__(self, base_url: str, model_name: str, system_prompt: str) -> None:
        """OpenAIを利用した AI Agentの初期化

        :param base_url OllamaのAPIが実行されているURL
        :param model_name 利用するLLMの名称
        :param system_prompt ユーザーの役割付けをするためのシステムプロンプト
        """
        self.client = Ollama(
            base_url=base_url,
            model=model_name,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        )
        self.system_prompt = system_prompt
        # 記憶を直近の10件まで保存
        self.histories: deque[tuple[str, str]] = deque(maxlen=10)

    def get_response(self, prompt: str) -> str:
        """AI からの応答を取得する

        :param str prompt: ユーザーから送られたメッセージ
        """
        self.histories.append((self.ROLE_USER, prompt))
        # Ollamaは文字列のみを渡すため、system_promptとユーザーからの投げかけをうまいこと組み合わせる必要がある
        # システムプロンプトは記憶から消してはダメなので、毎回初回に追加
        # TODO: 記憶には残せるようになったが、"出題"を確実に履歴に残せるようにしなければならない
        full_prompt = self.SYSTEM_PREFIX + self.system_prompt + self.SEPARATOR
        for role, message in self.histories:
            if role == self.ROLE_USER:
                full_prompt += self.USER_PREFIX + message + self.SEPARATOR
            elif role == self.ROLE_ASSISTANT:
                full_prompt += self.ASSISTANT_PREFIX + message + self.SEPARATOR
        response = self.client(full_prompt + self.ASSISTANT_PREFIX)
        self.histories.append((self.ROLE_ASSISTANT, response))
        logger.info(full_prompt)
        return response


# Factory クラス
class AgentFactory:
    """
    AI Agentを生成するFactoryクラス
    """

    def __init__(self, config: Settings) -> None:
        """AI Agentを生成するファクトリークラスの初期化

        :param config 設定ファイルの記載内容
        """
        self.config = config

    def create_agent(self, game_type: GameType, llm_type: LLMType) -> LLMAgent:
        """AI Agentを生成する

        :param game_type: 実行するゲームのEnum
        :param llm_type: 利用するLLMのEnum
        :return LLMAgentの仮想クラスを継承したインスタンス
        :raises NotImplementedError: game_typeやllm_typeが存在しないエラー
        """
        # まずは、システムプロンプトを作成
        system_prompt = system_prompts[game_type]
        if system_prompt is None:
            raise NotImplementedError(f"Game type {game_type} is not implemented")
        # そのプロンプトを基に、LLM Agentを作成
        match llm_type:
            case LLMType.OPEN_AI:
                return OpenAIAgent(
                    self.config.openai_api_key,
                    self.config.open_ai_chat_model,
                    system_prompt,
                )
            case LLMType.OLLAMA:
                return OllamaAgent(
                    self.config.ollama_base_url,
                    self.config.ollama_chat_model,
                    system_prompt,
                )
            case _:
                raise NotImplementedError(f"LLM type {llm_type} is not implemented")


# TODO: promptも、正しく自らについての、真実と嘘を認識させる工夫が必要
# また、promptも設定ファイルに含めるなど整理したい。
system_prompts = {
    GameType.TWO_TRUTH_A_LIE: """あなたは「2つの真実と1つの嘘」というゲームの進行役です。
    あなたの役割は、自分自身または与えられたトピックについて3つの文を生成することです。そのうち2つは真実で、1つは嘘です。以下のガイドラインに従ってください：

    1. 3つの異なる文を生成してください。
    2. 2つの文は真実の事実でなければなりません。
    3. 1つの文は真実と区別しにくい、もっともらしい嘘でなければなりません。
    4. 指定された場合、文は単一のトピックまたはテーマに関連していなければなりません。
    5. 簡単に識別できる明らかな嘘や真実は避けてください。
    6. 最初の回答では、どの文が嘘であるかを示さないでください。
    7. プレイヤーに尋ねられたら、どの文が嘘であるかを明かす準備をしてください。
    8. 特定のトピックやテーマが要求された場合、そのトピックに関連する文を生成してください。
    9. 社交ゲームにふさわしい、フレンドリーで魅力的な口調を維持してください。

    プロンプトが与えられたら、3つの文を生成し、プレイヤーがどれが嘘かを推測するのを待ってください。プレイヤーが推測した後、正解を明かし、各文について簡単な説明を提供してください。

    覚えておいてください。目標は、プレイヤーにとって魅力的で挑戦的なゲームを作ることです！"""
}
