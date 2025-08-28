from abc import ABC, abstractmethod
from typing import Dict, Any


class StreamMessaging(ABC):
    """Socket.io server로 video frame을 전송하기 위한 outbound port"""
    
    @abstractmethod
    async def send_video_frame(self, frame_data: bytes, metadata: Dict[str, Any] = None) -> None:
        """Socket.io server로 video frame 전송 (video_frame_from_service 이벤트)"""
        pass
    
    @abstractmethod
    async def emit_capture_status(self, status_data: Dict[str, Any]) -> None:
        """클라이언트에게 캡처 상태 직접 전송 (capture_status 이벤트)"""
        pass


class EventLogger(ABC):
    """Socket.io server로 로그 이벤트를 전송하기 위한 outbound port"""
    
    @abstractmethod
    async def log_event(self, event_type: str, client_id: str, metadata: Dict[str, Any] = None) -> None:
        """Socket.io server로 로그 이벤트 전송 (log_client_request 이벤트)"""
        pass