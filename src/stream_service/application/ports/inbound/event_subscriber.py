from abc import ABC, abstractmethod
from stream_service.application.dto.capture_dto import CaptureStatusDTO

class EventSubscriber(ABC):
    """Socket.io server로부터 받는 command를 처리하기 위한 inbound port"""
    
    
    @abstractmethod
    async def handle_request_client_metadata(self) -> None:    
        """client_metadata 요청 처리"""
        pass
    
    @abstractmethod
    async def handle_capture_start_request(self) -> None:
        """Capture 시작 command 처리"""
        pass
    
    @abstractmethod
    async def handle_capture_stop_request(self) -> None:
        """Capture 중지 command 처리"""
        pass
    
    @abstractmethod
    async def handle_request_capture_status(self) -> None:
        """현재 캡처 상태 조회"""
        pass
    
    
    
    
    
    
    
    
    