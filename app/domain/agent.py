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

    @abstractmethod
    def initialize_theme(self, directional_prompt: str) -> str:
        """Agentに指示を出してゲームのテーマを生成し、初回で出題した内容を記憶させる

        :param directional_prompt Agentに出題の指示を出すためのプロンプト
        :return 初回の指示を受けての回答。基本的にはゲームのテーマや出題となる
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
        self.directional_prompt = ""
        self.theme = ""
        self.histories = []

    def initialize_theme(self, directional_prompt: str) -> str:
        """Agentに指示を出してゲームのテーマを生成し、初回で出題した内容を記憶させる

        :param directional_prompt Agentに出題の指示を出すためのプロンプト
        :return 初回の指示を受けての回答。基本的にはゲームのテーマや出題となる
        """
        self.directional_prompt = directional_prompt
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": self.ROLE_SYSTEM, "content": self.system_prompt},
                {"role": self.ROLE_USER, "content": directional_prompt},
            ],
        )
        self.theme = response.choices[0].message.content
        return response.choices[0].message.content

    def get_response(self, prompt: str) -> str:
        """AI からの応答を取得する

        :param str prompt: ユーザーから送られたメッセージ
        """
        # TODO: できれば、RAGなどつけたい
        # ユーザーからのメッセージを履歴に追加
        self.histories.append({"role": self.ROLE_USER, "content": prompt})
        # 履歴のサイズを制限 (直近の10件)
        if len(self.histories) > 10:
            self.histories = self.histories[-10:]
        # システムプロンプト、初回の指示、指示を受けての回答と履歴を含むメッセージリストを構築
        messages = [{"role": self.ROLE_SYSTEM, "content": self.system_prompt}]
        messages = [{"role": self.ROLE_USER, "content": self.directional_prompt}]
        messages = [{"role": self.ROLE_ASSISTANT, "content": self.theme}]
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
        self.directional_prompt = ""
        self.theme = ""
        # 記憶を直近の10件まで保存
        self.histories: deque[tuple[str, str]] = deque(maxlen=10)

    def initialize_theme(self, directional_prompt: str) -> str:
        """Agentに指示を出してゲームのテーマを生成し、初回で出題した内容を記憶させる

        :param directional_prompt Agentに出題の指示を出すためのプロンプト
        :return 初回の指示を受けての回答。基本的にはゲームのテーマや出題となる
        """
        self.directional_prompt = directional_prompt
        response = self.client(
            self.SYSTEM_PREFIX
            + self.system_prompt
            + self.USER_PREFIX
            + self.directional_prompt
        )
        self.theme = response
        return response

    def get_response(self, prompt: str) -> str:
        """AI からの応答を取得する

        :param str prompt: ユーザーから送られたメッセージ
        """
        self.histories.append((self.ROLE_USER, prompt))
        # Ollamaは文字列のみを渡すため、system_promptとユーザーからの投げかけをうまいこと組み合わせる必要がある
        # システムプロンプトは記憶から消してはダメなので、毎回初回に追加
        # システムプロンプト、初回の指示、指示を受けての回答と履歴を含むメッセージリストを構築
        full_prompt = self.SYSTEM_PREFIX + self.system_prompt + self.SEPARATOR
        full_prompt += self.USER_PREFIX + self.directional_prompt + self.SEPARATOR
        full_prompt += self.ASSISTANT_PREFIX + self.theme + self.SEPARATOR
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
    GameType.TWO_TRUTH_A_LIE: """
As the host of "Two Truths and a Lie":

1. Generate three concise statements: two truths, one lie.
    - Topics: general knowledge, science, history, culture, sports
    - Make statements interesting, surprising, yet plausible
    - Ensure moderate difficulty and content randomness
    - Present statements directly, without numbering or labeling as truth/lie

2. Present statements directly, without introduction

3. If asked, provide brief details or background for each statement
    - Keep explanations short and engaging
    - Use light humor where appropriate

4. Respond to guesses with brief, amusing comments or hints
    - Never reveal which statement is the lie or truth

5. Maintain a lively, witty tone throughout

6. Address participants directly

7. Use text only, no emojis

8. Avoid confirmatory phrases (e.g., "Certainly", "Sure")

9. Keep all responses concise

Start the game immediately when prompted.
"""
}
