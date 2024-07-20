"""アプリケーションで共通の依存関係のあるモジュールをまとめる"""

from fastapi import Depends
from core.config import Settings
from services.websocket_service import WebsocketService
from domain.agent import AgentFactory


def get_settings() -> Settings:
    """.envに記載されている設定ファイルを取得する"""
    return Settings()


def get_agent_factory(settings: Settings = Depends(get_settings)) -> AgentFactory:
    return AgentFactory(settings)


def get_websocket_service(
    agent_factory: AgentFactory = Depends(get_agent_factory),
) -> WebsocketService:
    return WebsocketService(agent_factory)
