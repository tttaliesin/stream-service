from abc import ABC, abstractmethod
from application.dto.capture_dto import CaptureStatusDTO

class StreamHandler(ABC):
    """Socket.io server로부터 받는 command를 처리하기 위한 inbound port"""
    
    @abstractmethod
    async def handle_capture_start(self, client_id: str, metadata: dict = None) -> None:
        """Capture 시작 command 처리"""
        pass
    
    @abstractmethod
    async def handle_capture_stop(self, client_id: str, metadata: dict = None) -> None:
        """Capture 중지 command 처리"""
        pass
    
    @abstractmethod
    async def get_current_status(self) -> CaptureStatusDTO:
        """현재 캡처 상태 조회"""
        pass