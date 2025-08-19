from typing import Optional

from ...domain.models.capture_session import CaptureSession
from ...domain.services.capture_service import CaptureService


class CaptureUseCases:
    def __init__(self, capture_service: CaptureService):
        self.capture_service = capture_service
    
    async def start_capture(self) -> CaptureSession:
        """캡처 시작 유스케이스"""
        return await self.capture_service.start_capture()
    
    async def stop_capture(self) -> CaptureSession:
        """캡처 중지 유스케이스"""
        return await self.capture_service.stop_capture()
    
    def get_capture_status(self) -> CaptureSession:
        """현재 캡처 상태 조회 유스케이스"""
        return self.capture_service.get_status()
    
    async def get_current_frame(self) -> Optional[bytes]:
        """현재 프레임 조회 유스케이스"""
        return await self.capture_service.get_current_frame()