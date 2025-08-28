import logging
from typing import Dict, Any

from application.ports.inbound.stream_handler import StreamHandler
from adapters.outbound.messaging.socketio_streaming_adapter import SocketIOStreamingAdapter

logger = logging.getLogger(__name__)


class SocketIOCommandAdapter:
    """Socket.io server로부터 command를 수신하는 inbound adapter"""
    
    def __init__(self, stream_handler: StreamHandler, socketio_adapter: SocketIOStreamingAdapter):
        self.stream_handler = stream_handler
        self.socketio_adapter = socketio_adapter
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Socket.io 이벤트 핸들러를 socketio_adapter에 등록"""
        sio = self.socketio_adapter.sio
        
        @sio.event
        async def capture_start_request(data: Dict[str, Any]):
            client_id = data.get('client_id')
            metadata = data.get('metadata', {})
            
            logger.info(f"Received capture start command for client {client_id}")
            
            if client_id:
                try:
                    await self.stream_handler.handle_capture_start(client_id, metadata)
                except Exception as e:
                    logger.error(f"Error handling capture start for client {client_id}: {e}")
            else:
                logger.warning("Received capture start command without client_id")
        
        @sio.event
        async def capture_stop_request(data: Dict[str, Any]):
            client_id = data.get('client_id')
            metadata = data.get('metadata', {})
            
            logger.info(f"Received capture stop command for client {client_id}")
            
            if client_id:
                try:
                    await self.stream_handler.handle_capture_stop(client_id, metadata)
                except Exception as e:
                    logger.error(f"Error handling capture stop for client {client_id}: {e}")
            else:
                logger.warning("Received capture stop command without client_id")
        
        @sio.event
        async def capture_status_request(data: Dict[str, Any]):
            """현재 캡처 상태 요청에 대한 응답"""
            requesting_client = data.get('requesting_client')
            
            logger.info(f"Received capture status request for client {requesting_client}")
            
            if requesting_client:
                try:
                    # 현재 캡처 상태 조회
                    status = await self.stream_handler.get_current_status()
                    
                    # event-manage-service에 응답 전송
                    await self.socketio_adapter.emit_capture_status_response({
                        'requesting_client': requesting_client,
                        'is_active': status.is_active,
                        'rtsp_url': status.rtsp_url,
                        'error_message': status.error_message
                    })
                    
                    logger.info(f"Sent capture status response for client {requesting_client}")
                    
                except Exception as e:
                    logger.error(f"Error getting capture status: {e}")
                    # 에러 상태로 응답
                    await self.socketio_adapter.emit_capture_status_response({
                        'requesting_client': requesting_client,
                        'is_active': False,
                        'rtsp_url': '',
                        'error_message': str(e)
                    })
            else:
                logger.warning("Received capture status request without requesting_client")