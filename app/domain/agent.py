"""AI Agentのドメイン管理とビジネスロジックを管理している
"""

from abc import ABC, abstractmethod
import logging
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
        """
        LLMモデルに対してプロンプトを入力し、応答を取得する
        """


class OpenAIAgent(LLMAgent):
    """Open AIを使ったAI Agent"""

    def __init__(self, api_key: str, model_name: str, system_prompt: str) -> None:
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = system_prompt
        self.histories = []

    def get_response(self, prompt: str) -> str:
        """AI からの応答を取得する

        :param str prompt: ユーザーから送られたメッセージ
        """
        # TODO: historiesに履歴を入れて、ユーザーからのメッセージを保存しておく
        # TODO: できれば、RAGなどつけたい
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e
        return response.choices[0].message.content


class OllamaAgent(LLMAgent):
    """ollamaを使ったAI Agent"""

    def __init__(self, base_url: str, model_name: str, system_prompt: str) -> None:
        self.client = Ollama(
            base_url=base_url,
            model=model_name,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        )
        self.system_prompt = system_prompt
        self.histories = []

    def get_response(self, prompt: str) -> str:
        # system_promptとユーザーからの投げかけをうまいこと組み合わせる必要がある
        # TODO: historiesに履歴を入れて、ユーザーからのメッセージを保存しておく
        # TODO: とりあえず、ローカル変数で格納。構成の整理はしたい
        system_prefix = "[system]\n"
        user_prefix = "[user]\n"
        asistant_prefix = "[asistant]\n"
        separator = "\n\n"
        return self.client(
            system_prefix
            + self.system_prompt
            + separator
            + user_prefix
            + prompt
            + separator
            + asistant_prefix
        )


# Factory クラス
class AgentFactory:
    """
    AI Agentを生成するFactoryクラス
    """

    def __init__(self, config: Settings) -> None:
        self.config = config

    def create_agent(self, game_type: GameType, llm_type: LLMType) -> LLMAgent:
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
    GameType.TOW_TRUTH_A_LIE: """あなたは「2つの真実と1つの嘘」というゲームの進行役です。
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
