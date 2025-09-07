from stream_service.domain.models.capture_session import CaptureSession


class CaptureService:
    def __init__(
        self, 
        rtsp_url: str = "rtsp://210.99.70.120:1935/live/cctv003.stream"
    ):
        self.session = CaptureSession.create(rtsp_url)
    
    def start_capture_session(self) -> CaptureSession:
        """캡처 세션 시작 (비즈니스 규칙 검증)"""
        if not self.session.can_start:
            raise ValueError(f"Cannot start capture in status: {self.session.status}")
        
        self.session.start()
        return self.session
    
    def mark_capture_running(self) -> CaptureSession:
        """캡처를 실행 중으로 표시"""
        self.session.mark_running()
        return self.session
    
    def stop_capture_session(self) -> CaptureSession:
        """캡처 세션 중지 (비즈니스 규칙 검증)"""
        if not self.session.can_stop:
            raise ValueError(f"Cannot stop capture in status: {self.session.status}")
        
        self.session.stop()
        return self.session
    
    def mark_capture_stopped(self) -> CaptureSession:
        """캡처를 중지됨으로 표시"""
        self.session.mark_stopped()
        return self.session
    
    def mark_capture_error(self, error_message: str) -> CaptureSession:
        """캡처 에러 표시"""
        self.session.mark_error(error_message)
        return self.session
    
    def get_session_status(self) -> CaptureSession:
        """현재 캡처 세션 상태 반환"""
        return self.session