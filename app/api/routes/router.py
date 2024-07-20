import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from core.connection import Connection
from api.dependencies import get_websocket_service

# import asyncio

api_router = APIRouter()
logger = logging.getLogger(__name__)
connection = Connection()


@api_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, websocket_service=Depends(get_websocket_service)
):
    """WebSocket接続用のエンドポイント"""
    await connection.connect(websocket)
    # youtubeなどでコメントを取得して、何かをしたい場合は、非同期のtaskを作成してウォッチすることが可能
    # asyncio.create_task(communicate_comments(video_id, api_key))
    try:
        while True:
            message = await websocket.receive_text()
            logger.info("Message text is: %s", message)
            await websocket_service.handle_message(message, connection)
    except WebSocketDisconnect:
        connection.disconnect(websocket)
        logger.info("WebSocket disconnected")
