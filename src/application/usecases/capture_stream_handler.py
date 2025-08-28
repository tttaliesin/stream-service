from domain.services.capture_service import CaptureService
from application.ports.inbound.stream_handler import StreamHandler
from application.ports.outbound.stream_messaging import StreamMessaging, EventLogger
from application.dto.capture_dto import CaptureStatusDTO


class CaptureStreamHandler(StreamHandler):
    def __init__(self, capture_service: CaptureService, stream_messaging: StreamMessaging, event_logger: EventLogger):
        self.capture_service = capture_service
        self.stream_messaging = stream_messaging
        self.event_logger = event_logger
        
        # CaptureService에 프레임 콜백 설정
        self.capture_service.set_frame_callback(self.send_frame_to_stream_server)
    
    async def handle_capture_start(self, client_id: str, metadata: dict = None) -> None:
        """Socket.io server로부터 받은 capture start command 처리"""
        try:
            await self.event_logger.log_event("capture_start_command", client_id, metadata)
            
            session = await self.capture_service.start_capture()
            
            # 클라이언트에게 캡처 시작 상태 직접 전송
            await self.stream_messaging.emit_capture_status({
                'is_active': session.is_active,
                'rtsp_url': session.rtsp_url
            })
            
            await self.event_logger.log_event("capture_started", client_id, {"success": True})
        except Exception as e:
            # 에러 상태도 클라이언트에게 전송
            await self.stream_messaging.emit_capture_status({
                'is_active': False,
                'rtsp_url': '',
                'error_message': str(e)
            })
            await self.event_logger.log_event("capture_start_failed", client_id, {"error": str(e)})
            raise
    
    async def handle_capture_stop(self, client_id: str, metadata: dict = None) -> None:
        """Socket.io server로부터 받은 capture stop command 처리"""
        try:
            await self.event_logger.log_event("capture_stop_command", client_id, metadata)
            
            session = await self.capture_service.stop_capture()
            
            # 클라이언트에게 캡처 중지 상태 직접 전송
            await self.stream_messaging.emit_capture_status({
                'is_active': session.is_active,
                'rtsp_url': session.rtsp_url
            })
            
            await self.event_logger.log_event("capture_stopped", client_id, {"success": True})
        except Exception as e:
            # 에러 상태도 클라이언트에게 전송
            await self.stream_messaging.emit_capture_status({
                'is_active': False,
                'rtsp_url': '',
                'error_message': str(e)
            })
            await self.event_logger.log_event("capture_stop_failed", client_id, {"error": str(e)})
            raise
    
    async def get_current_status(self) -> CaptureStatusDTO:
        """현재 캡처 상태 조회"""
        session = self.capture_service.get_status()
        return CaptureStatusDTO.from_domain(session)
    
    async def send_frame_to_stream_server(self, frame_data: bytes) -> None:
        """Socket.io server로 video frame 전송"""
        try:
            await self.stream_messaging.send_video_frame(frame_data)
        except Exception as e:
            # 로깅만 하고 예외를 다시 발생시키지 않음 (스트리밍 중단 방지)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending frame to stream server: {e}")