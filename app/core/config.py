""" 設定ファイルを読み込むためのモジュール.ここで設定周りは共通化しておく """

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """設定ファイルをまとめるためのクラス"""

    app_name: str = "AI Reception API"
    openai_api_key: str
    open_ai_chat_model: str
    ollama_base_url: str
    ollama_chat_model: str

    class Config:
        """pydanticでの予約クラス.特定のファイルから環境変数を読み込める"""

        env_file = ".env"
