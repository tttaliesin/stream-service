import asyncio
import base64
import logging
from typing import AsyncGenerator, Optional

import cv2

from ....domain.ports.capture_engine import CaptureEngine

logger = logging.getLogger(__name__)


class OpenCVCaptureEngine(CaptureEngine):
    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_capturing = False
        self._frame_rate = 30  # FPS
        self._frame_interval = 1.0 / self._frame_rate
    
    async def start_capture(self, rtsp_url: str) -> None:
        """RTSP 스트림 캡처 시작"""
        if self._is_capturing:
            raise RuntimeError("Capture is already running")
        
        logger.info(f"Starting RTSP capture from {rtsp_url}")
        
        # OpenCV VideoCapture는 동기 작업이므로 executor에서 실행
        loop = asyncio.get_event_loop()
        
        def _open_capture():
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                raise RuntimeError(f"Failed to open RTSP stream: {rtsp_url}")
            
            # RTSP 스트림 설정 최적화
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화 (지연 감소)
            cap.set(cv2.CAP_PROP_FPS, self._frame_rate)
            
            return cap
        
        try:
            self._cap = await loop.run_in_executor(None, _open_capture)
            self._is_capturing = True
            logger.info("RTSP capture started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start RTSP capture: {e}")
            self._cleanup()
            raise
    
    async def stop_capture(self) -> None:
        """RTSP 스트림 캡처 중지"""
        if not self._is_capturing:
            return
        
        logger.info("Stopping RTSP capture")
        self._cleanup()
        logger.info("RTSP capture stopped")
    
    async def get_current_frame(self) -> Optional[bytes]:
        """현재 프레임을 JPEG 바이너리로 반환"""
        if not self._is_capturing or not self._cap:
            return None
        
        loop = asyncio.get_event_loop()
        
        def _read_frame():
            ret, frame = self._cap.read()
            if not ret or frame is None:
                return None
            
            # 프레임을 JPEG로 인코딩
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not success:
                return None
            
            return buffer.tobytes()
        
        try:
            return await loop.run_in_executor(None, _read_frame)
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None
    
    def is_capturing(self) -> bool:
        """현재 캡처 중인지 확인"""
        return self._is_capturing
    
    async def frame_stream(self) -> AsyncGenerator[bytes, None]:
        """실시간 프레임 스트림"""
        if not self._is_capturing:
            logger.warning("Cannot start frame stream: capture is not running")
            return
        
        logger.info("Starting frame stream")
        
        while self._is_capturing and self._cap:
            try:
                frame_data = await self.get_current_frame()
                
                if frame_data:
                    # Base64 인코딩하여 JSON으로 전송 가능하게 만듦
                    base64_frame = base64.b64encode(frame_data).decode('utf-8')
                    yield base64_frame.encode('utf-8')
                
                # 프레임 레이트 제어
                await asyncio.sleep(self._frame_interval)
                
            except asyncio.CancelledError:
                logger.info("Frame stream cancelled")
                break
            except Exception as e:
                logger.error(f"Error in frame stream: {e}")
                await asyncio.sleep(1)  # 에러 시 잠시 대기
        
        logger.info("Frame stream ended")
    
    def _cleanup(self) -> None:
        """리소스 정리"""
        self._is_capturing = False
        
        if self._cap:
            try:
                self._cap.release()
            except Exception as e:
                logger.error(f"Error releasing capture: {e}")
            finally:
                self._cap = None
    
    def __del__(self):
        """소멸자에서 리소스 정리"""
        self._cleanup()