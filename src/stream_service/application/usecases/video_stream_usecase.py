import asyncio
import logging
from typing import Callable, Optional

from stream_service.domain.services.capture_service import CaptureService

logger = logging.getLogger(__name__)
from stream_service.application.ports.inbound.event_subscriber import EventSubscriber
from stream_service.application.ports.outbound.event_publisher import EventPublisher
from stream_service.application.dto.socketio_dto import (
    ResponseClientMetadataDTO,
    CaptureStatusResponseDTO,
)
from stream_service.application.ports.outbound.capture_engine import CaptureEngine


class VideoStreamUseCase(EventSubscriber):
    def __init__(
        self, 
        capture_service: CaptureService, 
        event_publisher: EventPublisher, 
        capture_engine: CaptureEngine
    ):
        self.capture_service = capture_service
        self.event_publisher = event_publisher
        self.capture_engine = capture_engine
        
        self._frame_task = None
        self._frame_callback = self._send_frame_via_socketio
    
    async def _send_frame_via_socketio(self, frame_data: bytes) -> None:
        """Socket.IO를 통해 프레임 전송"""
        from stream_service.application.dto.socketio_dto import VideoFrameFromServiceDTO
        dto = VideoFrameFromServiceDTO(frame_data=frame_data)
        await self.event_publisher.send_video_frame(dto)
    
    async def handle_request_client_metadata(self) -> None:
        dto = ResponseClientMetadataDTO(
            client_type='stream-service'
        )
        await self.event_publisher.response_client_metadata(dto)
    
    async def handle_capture_start_request(self) -> None:
        try:
            session = self.capture_service.start_capture_session()
            
            await self.capture_engine.start_capture(session.rtsp_url)
            self.capture_service.mark_capture_running()
            
            logger.info("Capture session marked as running, starting frame streaming task")
            
            self._frame_task = asyncio.create_task(self._stream_frames())
            logger.info("Frame streaming task created")
            
            dto = CaptureStatusResponseDTO(
                status=session.status.value,
                rtsp_url=session.rtsp_url,
                is_active=session.is_active
            )
            await self.event_publisher.emit_capture_status(dto)
            
        except Exception as e:
            self.capture_service.mark_capture_error(str(e))
            raise
    
    async def handle_capture_stop_request(self) -> None:
        try:
            session = self.capture_service.stop_capture_session()
            
            if self._frame_task:
                self._frame_task.cancel()
                try:
                    await self._frame_task
                except asyncio.CancelledError:
                    pass
                self._frame_task = None
            
            await self.capture_engine.stop_capture()
            self.capture_service.mark_capture_stopped()
            
            dto = CaptureStatusResponseDTO(
                status=session.status.value,
                rtsp_url=session.rtsp_url,
                is_active=session.is_active
            )
            await self.event_publisher.emit_capture_status(dto)
            
        except Exception as e:
            self.capture_service.mark_capture_error(str(e))
            raise
    
    async def handle_request_capture_status(self) -> None:
        session = self.capture_service.get_session_status()
        dto = CaptureStatusResponseDTO(
            status=session.status,
            rtsp_url=session.rtsp_url,
        )
        await self.event_publisher.emit_capture_status(dto)
    
    async def _stream_frames(self) -> None:
        """백그라운드에서 프레임 스트리밍"""
        logger.info("Frame streaming loop started")
        
        try:
            frame_rate = 30  # FPS
            frame_interval = 1.0 / frame_rate
            frame_count = 0
            
            session = self.capture_service.get_session_status()
            while session.is_active:
                frame_data = await self.capture_engine.get_current_frame()
                if frame_data and self._frame_callback:
                    try:
                        await self._frame_callback(frame_data)
                        frame_count += 1
                        if frame_count % 30 == 0:
                            logger.info(f"Sent {frame_count} frames to Socket.IO server")
                    except Exception as e:
                        logger.error(f"Frame callback error: {e}")
                elif not frame_data:
                    logger.warning("No frame data received from capture engine")
                elif not self._frame_callback:
                    logger.warning("No frame callback set")
                
                await asyncio.sleep(frame_interval)
                session = self.capture_service.get_session_status()
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.capture_service.mark_capture_error(f"Frame streaming error: {str(e)}")
