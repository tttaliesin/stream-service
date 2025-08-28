from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional


class CaptureEngine(ABC):
    @abstractmethod
    async def start_capture(self, rtsp_url: str) -> None:
        """RTSP 스트림 캡처 시작"""
        pass
    
    @abstractmethod
    async def stop_capture(self) -> None:
        """RTSP 스트림 캡처 중지"""
        pass
    
    @abstractmethod
    async def get_current_frame(self) -> Optional[bytes]:
        """현재 프레임을 바이너리로 반환"""
        pass
    
    @abstractmethod
    def is_capturing(self) -> bool:
        """현재 캡처 중인지 확인"""
        pass
    
    @abstractmethod
    async def frame_stream(self) -> AsyncGenerator[bytes, None]:
        """실시간 프레임 스트림"""
        pass