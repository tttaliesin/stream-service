from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CaptureStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class CaptureSession:
    rtsp_url: str
    status: CaptureStatus
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    error_message: Optional[str]
    
    @classmethod
    def create(cls, rtsp_url: str) -> "CaptureSession":
        return cls(
            rtsp_url=rtsp_url,
            status=CaptureStatus.STOPPED,
            started_at=None,
            stopped_at=None,
            error_message=None,
        )
    
    def start(self) -> None:
        if self.status in [CaptureStatus.STARTING, CaptureStatus.RUNNING]:
            raise ValueError("capture가 이미 시작 중입니다.")
        
        self.status = CaptureStatus.STARTING
        self.started_at = datetime.now()
        self.stopped_at = None
        self.error_message = None
    
    def mark_running(self) -> None:
        if self.status != CaptureStatus.STARTING:
            raise ValueError("Cannot mark as running when not starting")
        
        self.status = CaptureStatus.RUNNING
    
    def stop(self) -> None:
        if self.status in [CaptureStatus.STOPPED, CaptureStatus.STOPPING]:
            raise ValueError("Capture is already stopped or stopping")
        
        self.status = CaptureStatus.STOPPING
    
    def mark_stopped(self) -> None:
        if self.status != CaptureStatus.STOPPING:
            raise ValueError("Cannot mark as stopped when not stopping")
        
        self.status = CaptureStatus.STOPPED
        self.stopped_at = datetime.now()
    
    def mark_error(self, error_message: str) -> None:
        self.status = CaptureStatus.ERROR
        self.error_message = error_message
        self.stopped_at = datetime.now()
    
    @property
    def is_active(self) -> bool:
        return self.status in [CaptureStatus.STARTING, CaptureStatus.RUNNING]
    
    @property
    def can_start(self) -> bool:
        return self.status in [CaptureStatus.STOPPED, CaptureStatus.ERROR]
    
    @property
    def can_stop(self) -> bool:
        return self.status in [CaptureStatus.STARTING, CaptureStatus.RUNNING]