import logging
from typing import Dict, Any
import socketio

from stream_service.application.ports.inbound.event_subscriber import EventSubscriber
from stream_service.adapters.outbound.messaging.socketio_publisher import SocketIOPublisher

logger = logging.getLogger(__name__)


class SocketIOClient:
    """Socket.io server로부터 command를 수신하는 inbound adapter"""
    
    def __init__(self, 
                 sio: socketio.AsyncClient,
                 event_subscriber: EventSubscriber
    ):
        self.sio = sio
        self.event_subscriber = event_subscriber
    
    def resister_event(self) -> None:
        """Socket.io 이벤트 핸들러를 socketio_adapter에 등록"""
        @self.sio.event
        async def request_client_metadata():
            """ client의 ResponseClientMetadataDTO를 요청 받았습니다."""
            logger.info("client의 ResponseClientMetadataDTO를 요청 받았습니다.")
            await self.event_subscriber.handle_request_client_metadata()
        
        @self.sio.event
        async def capture_start_request():
            """ stream_service의 capture start를 요청 받았습니다.""" 
            logger.info("stream_service의 capture start를 요청 받았습니다.")
            await self.event_subscriber.handle_capture_start_request()
         
        
        @self.sio.event
        async def capture_stop_request():
            """ stream_service의 capture stop 요청 받았습니다.""" 
            logger.info("stream_service의 capture stop 요청 받았습니다.")
            await self.event_subscriber.handle_capture_stop_request()
            
        @self.sio.event
        async def request_capture_status():
            """ stream_service의 현재 capture status를 요청 받았습니다.""" 
            logger.info("stream_service의 현재 capture status를 요청 받았습니다.")
            await self.event_subscriber.handle_request_capture_status()
            
    