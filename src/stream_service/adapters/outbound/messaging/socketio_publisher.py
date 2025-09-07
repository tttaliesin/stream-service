import logging
import socketio
import asyncio
from typing import Dict, Any

from stream_service.application.ports.outbound.event_publisher import EventPublisher

from stream_service.config.constants import EmitEvent
from stream_service.application.dto.socketio_dto import (
    ResponseClientMetadataDTO,
    VideoFrameFromServiceDTO,
    CaptureStatusResponseDTO
)
logger = logging.getLogger(__name__)

class SocketIOPublisher(EventPublisher):
    def __init__(
        self, 
        sio: socketio.AsyncClient,
        emit_event: EmitEvent
    ):
        self.sio = sio
        self._connected = False
        self.emit_event = emit_event
    
    async def response_client_metadata(self, dto: ResponseClientMetadataDTO) -> None:
        data = dto.model_dump()
        logger.info("네임스페이스 연결 대기")
        await asyncio.sleep(1)
        logger.info("stream_service client ResponseClientMetadataDTO 전송")
        await self.sio.emit(
            self.emit_event.RESPONSE_CLIENT_METADATA,
            data
        )

    async def send_video_frame(self, dto: VideoFrameFromServiceDTO) -> None:
        data = dto.model_dump()
        await self.sio.emit(
            self.emit_event.VIDEO_FRAME_RELAY,
            data
        )
    
    async def emit_capture_status(self, dto: CaptureStatusResponseDTO) -> None:
        data = dto.model_dump()
        await self.sio.emit(
            self.emit_event.BROADCAST_CAPTURE_STATUS,
            data
        )