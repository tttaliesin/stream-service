import asyncio
from typing import Callable, Optional

from domain.models.capture_session import CaptureSession, CaptureStatus
from application.ports.outbound.capture_engine import CaptureEngine


class CaptureService:
    def __init__(
        self, 
        capture_engine: CaptureEngine, 
        rtsp_url: str = "rtsp://210.99.70.120:1935/live/cctv003.stream"
    ):
        self.capture_engine = capture_engine
        self.session = CaptureSession.create(rtsp_url)
        self._frame_task = None
        self._frame_callback: Optional[Callable[[bytes], None]] = None
    
    def set_frame_callback(self, callback: Callable[[bytes], None]) -> None:
        """프레임 전송을 위한 콜백 설정"""
        self._frame_callback = callback
    
    async def start_capture(self) -> CaptureSession:
        """캡처 시작"""
        if not self.session.can_start:
            raise ValueError(f"Cannot start capture in status: {self.session.status}")
        
        try:
            self.session.start()
            
            await self.capture_engine.start_capture(self.session.rtsp_url)
            self.session.mark_running()
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Capture session marked as running, starting frame streaming task")
            
            # 프레임 스트리밍 백그라운드 태스크 시작
            self._frame_task = asyncio.create_task(self._stream_frames())
            logger.info("Frame streaming task created")
            
            return self.session
            
        except Exception as e:
            self.session.mark_error(str(e))
            raise
    
    async def stop_capture(self) -> CaptureSession:
        """캡처 중지"""
        if not self.session.can_stop:
            raise ValueError(f"Cannot stop capture in status: {self.session.status}")
        
        try:
            self.session.stop()
            
            # 프레임 스트리밍 태스크 중지
            if self._frame_task:
                self._frame_task.cancel()
                try:
                    await self._frame_task
                except asyncio.CancelledError:
                    pass
                self._frame_task = None
            
            await self.capture_engine.stop_capture()
            self.session.mark_stopped()
            
            return self.session
            
        except Exception as e:
            self.session.mark_error(str(e))
            raise
    
    def get_status(self) -> CaptureSession:
        """현재 캡처 상태 반환"""
        return self.session
    
    
    async def _stream_frames(self) -> None:
        """백그라운드에서 프레임 스트리밍"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Frame streaming loop started")
        
        try:
            frame_rate = 30  # FPS
            frame_interval = 1.0 / frame_rate
            frame_count = 0
            
            while self.session.is_active:
                frame_data = await self.capture_engine.get_current_frame()
                if frame_data and self._frame_callback:
                    try:
                        await self._frame_callback(frame_data)
                        frame_count += 1
                        if frame_count % 30 == 0:  # 매 30프레임마다 로그
                            logger.info(f"Sent {frame_count} frames to Socket.IO server")
                    except Exception as e:
                        # 프레임 전송 실패는 로깅만 하고 스트리밍 계속
                        logger.error(f"Frame callback error: {e}")
                elif not frame_data:
                    logger.warning("No frame data received from capture engine")
                elif not self._frame_callback:
                    logger.warning("No frame callback set")
                
                # 프레임 레이트 제어
                await asyncio.sleep(frame_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.session.mark_error(f"Frame streaming error: {str(e)}")