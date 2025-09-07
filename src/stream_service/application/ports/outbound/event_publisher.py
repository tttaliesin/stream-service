from abc import ABC, abstractmethod
from typing import Dict, Any
from stream_service.application.dto.socketio_dto import (
    ResponseClientMetadataDTO,
    VideoFrameFromServiceDTO,
    CaptureStatusResponseDTO
)


class EventPublisher(ABC):
    """Socket.io server로 video frame을 전송하기 위한 outbound port"""
    
    @abstractmethod
    async def response_client_metadata(self, dto: ResponseClientMetadataDTO) -> None:
        """Connect 핸드쉐이크로 Socket.io server에 클라이언트 정보 전송"""
        pass
        
    
    @abstractmethod
    async def send_video_frame(self, dto: VideoFrameFromServiceDTO) -> None:
        """Socket.io server로 video frame 전송 (video_frame_from_service 이벤트)"""
        pass
    
    @abstractmethod
    async def emit_capture_status(self, dto: CaptureStatusResponseDTO) -> None:
        """클라이언트에게 캡처 상태 직접 전송 (capture_status 이벤트)"""
        pass