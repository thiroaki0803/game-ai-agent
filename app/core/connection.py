"""Websocketのコネクションを管理・操作するためのコアモジュール
"""

from fastapi import WebSocket


class Connection:
    """Websocketのコネクションを管理・操作するためのクラス"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Websocketのコネクションを確立する関数

        コネクションを確立し、broadcastをするために、リストとして管理する

        :param websocket Websocketの操作に必要なライブラリ
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Websocketのコネクションを破棄したときに実行される

        アクティブなコネクションのリストから削除する

        :param websocket Websocketの操作に必要なライブラリ
        """
        self.active_connections.remove(websocket)

    async def send_text(self, message: str, websocket: WebSocket) -> None:
        """個別のユーザーにメッセージを送信する

        :param message 送信するメッセージ
        :param websocket Websocketの操作に必要なライブラリ
        """
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        """すべてのユーザーにメッセージを送信する

        :param message 送信するメッセージ
        """
        for connection in self.active_connections:
            await connection.send_text(message)
