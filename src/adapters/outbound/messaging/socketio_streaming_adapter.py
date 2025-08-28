import logging
import socketio
from typing import Dict, Any

from application.ports.outbound.stream_messaging import StreamMessaging, EventLogger

logger = logging.getLogger(__name__)

class SocketIOStreamingAdapter(StreamMessaging, EventLogger):
    
    def __init__(self, socketio_url: str = "http://localhost:8001"):
        self.socketio_url = socketio_url
        self.sio = socketio.AsyncClient()
        self._connected = False
    
    async def connect(self) -> None:
        if self._connected:
            return
        try:
            logger.info(f"Connecting to Socket.io server at {self.socketio_url}")
            await self.sio.connect(f"{self.socketio_url}?type=service")
            self._connected = True
            logger.info("Successfully connected to Socket.io server and joined service_room")
        except Exception as e:
            logger.error(f"Failed to connect to Socket.io server: {e}")
            raise
    
    async def disconnect(self) -> None:
        if not self._connected:
            return
        
        try:
            await self.sio.disconnect()
            self._connected = False
            logger.info("Disconnected from Socket.io server")
        except Exception as e:
            logger.error(f"Error disconnecting from Socket.io server: {e}")
    
    async def send_video_frame(self, frame_data: bytes, metadata: Dict[str, Any] = None) -> None:
        if not self._connected:
            logger.warning("Not connected to Socket.io server, cannot send video frame")
            return
        
        try:
            await self.sio.emit('video_frame_from_service', {
                'frame_data': frame_data,
                'metadata': metadata or {}
            })
            logger.debug("Video frame sent to Socket.io server")
        except Exception as e:
            logger.error(f"Error sending video frame: {e}")
    
    async def log_event(self, event_type: str, client_id: str, metadata: Dict[str, Any] = None) -> None:
        if not self._connected:
            logger.warning("Not connected to Socket.io server, cannot send log event")
            return
        
        try:
            await self.sio.emit('log_client_request', {
                'event_type': event_type,
                'client_id': client_id,
                'metadata': metadata or {}
            })
            logger.debug(f"Log event sent to Socket.io server: {event_type} for client {client_id}")
        except Exception as e:
            logger.error(f"Error sending log event: {e}")
    
    async def emit_capture_status_response(self, status_data: Dict[str, Any]) -> None:
        """캡처 상태 응답을 event-manage-service에 전송"""
        if not self._connected:
            logger.warning("Not connected to Socket.io server, cannot send capture status response")
            return
        
        try:
            await self.sio.emit('get_capture_status_response', status_data)
            logger.debug(f"Capture status response sent to Socket.io server for client {status_data.get('requesting_client')}")
        except Exception as e:
            logger.error(f"Error sending capture status response: {e}")
    
    async def emit_capture_status(self, status_data: Dict[str, Any]) -> None:
        """클라이언트에게 캡처 상태 직접 전송"""
        if not self._connected:
            logger.warning("Not connected to Socket.io server, cannot send capture status")
            return
        
        try:
            # event-manage-service의 client_room으로 브로드캐스트 요청
            await self.sio.emit('broadcast_capture_status', {
                'event': 'capture_status',
                'data': status_data
            })
            logger.debug(f"Capture status broadcast request sent for client {status_data.get('client_id')}")
        except Exception as e:
            logger.error(f"Error sending capture status broadcast request: {e}")
    
    def is_connected(self) -> bool:
        return self._connected and self.sio.connected