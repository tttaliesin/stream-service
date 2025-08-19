import asyncio
from typing import Optional

from ..models.capture_session import CaptureSession, CaptureStatus
from ..ports.capture_engine import CaptureEngine
from ..ports.websocket_broadcaster import SocketIOBroadcaster


class CaptureService:
    def __init__(
        self, 
        capture_engine: CaptureEngine, 
        socketio_broadcaster: SocketIOBroadcaster,
        rtsp_url: str = "rtsp://210.99.70.120:1935/live/cctv006.streamd"
    ):
        self.capture_engine = capture_engine
        self.socketio_broadcaster = socketio_broadcaster
        self.session = CaptureSession.create(rtsp_url)
        self._frame_task: Optional[asyncio.Task] = None
    
    async def start_capture(self) -> CaptureSession:
        """캡처 시작"""
        if not self.session.can_start:
            raise ValueError(f"Cannot start capture in status: {self.session.status}")
        
        try:
            self.session.start()
            await self._broadcast_status()
            
            await self.capture_engine.start_capture(self.session.rtsp_url)
            self.session.mark_running()
            
            # 프레임 스트리밍 백그라운드 태스크 시작
            self._frame_task = asyncio.create_task(self._stream_frames())
            
            await self._broadcast_status()
            return self.session
            
        except Exception as e:
            self.session.mark_error(str(e))
            await self._broadcast_status()
            raise
    
    async def stop_capture(self) -> CaptureSession:
        """캡처 중지"""
        if not self.session.can_stop:
            raise ValueError(f"Cannot stop capture in status: {self.session.status}")
        
        try:
            self.session.stop()
            await self._broadcast_status()
            
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
            
            await self._broadcast_status()
            return self.session
            
        except Exception as e:
            self.session.mark_error(str(e))
            await self._broadcast_status()
            raise
    
    def get_status(self) -> CaptureSession:
        """현재 캡처 상태 반환"""
        return self.session
    
    async def get_current_frame(self) -> Optional[bytes]:
        """현재 프레임 반환"""
        if not self.session.is_active:
            return None
        return await self.capture_engine.get_current_frame()
    
    async def _stream_frames(self) -> None:
        """백그라운드에서 프레임 스트리밍"""
        try:
            async for frame in self.capture_engine.frame_stream():
                await self.socketio_broadcaster.broadcast_frame(frame)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.session.mark_error(f"Frame streaming error: {str(e)}")
            await self._broadcast_status()
    
    async def _broadcast_status(self) -> None:
        """상태 변경을 Socket.IO로 브로드캐스트"""
        status_data = {
            "status": self.session.status.value,
            "rtsp_url": self.session.rtsp_url,
            "is_active": self.session.is_active,
            "started_at": self.session.started_at.isoformat() if self.session.started_at else None,
            "stopped_at": self.session.stopped_at.isoformat() if self.session.stopped_at else None,
            "error_message": self.session.error_message,
        }
        await self.socketio_broadcaster.broadcast_status(status_data)