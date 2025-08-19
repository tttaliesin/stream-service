import logging
from typing import Any, Dict, Set

import socketio

from ....domain.ports.websocket_broadcaster import SocketIOBroadcaster

logger = logging.getLogger(__name__)


class SocketIOBroadcasterImpl(SocketIOBroadcaster):
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self._connected_clients: Set[str] = set()
    
    async def broadcast_status(self, status: Dict[str, Any]) -> None:
        """캡처 상태를 모든 연결된 클라이언트에게 브로드캐스트"""
        if not self._connected_clients:
            logger.debug("No connected clients to broadcast status")
            return
        
        try:
            await self.sio.emit('capture_status', status)
            logger.debug(f"Broadcasted status to {len(self._connected_clients)} clients")
        except Exception as e:
            logger.error(f"Error broadcasting status: {e}")
    
    async def broadcast_frame(self, frame_data: bytes) -> None:
        """프레임 데이터를 모든 연결된 클라이언트에게 브로드캐스트"""
        if not self._connected_clients:
            logger.debug("No connected clients to broadcast frame")
            return
        
        try:
            # frame_data는 이미 base64 인코딩된 bytes
            frame_str = frame_data.decode('utf-8')
            await self.sio.emit('frame_data', {'image': frame_str})
            logger.debug(f"Broadcasted frame to {len(self._connected_clients)} clients")
        except Exception as e:
            logger.error(f"Error broadcasting frame: {e}")
    
    async def emit_to_client(self, sid: str, event: str, data: Any) -> None:
        """특정 클라이언트에게 이벤트 전송"""
        try:
            await self.sio.emit(event, data, room=sid)
            logger.debug(f"Sent {event} to client {sid}")
        except Exception as e:
            logger.error(f"Error sending {event} to client {sid}: {e}")
    
    def add_client(self, sid: str) -> None:
        """새 클라이언트 추가"""
        self._connected_clients.add(sid)
        logger.info(f"Client {sid} connected. Total clients: {len(self._connected_clients)}")
    
    def remove_client(self, sid: str) -> None:
        """클라이언트 제거"""
        self._connected_clients.discard(sid)
        logger.info(f"Client {sid} disconnected. Total clients: {len(self._connected_clients)}")
    
    def get_connected_count(self) -> int:
        """연결된 클라이언트 수 반환"""
        return len(self._connected_clients)
    
    def is_any_connected(self) -> bool:
        """연결된 클라이언트가 있는지 확인"""
        return len(self._connected_clients) > 0