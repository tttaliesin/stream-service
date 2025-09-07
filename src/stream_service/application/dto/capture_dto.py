from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from domain.models.capture_session import CaptureSession


class CaptureStatusDTO(BaseModel):
    """캡처 상태 응답 DTO"""
    status: str
    rtsp_url: str
    is_active: bool
    started_at: Optional[str]
    stopped_at: Optional[str]
    error_message: Optional[str]

    @classmethod
    def from_domain(cls, session: CaptureSession) -> "CaptureStatusDTO":
        return cls(
            status=session.status.value,
            rtsp_url=session.rtsp_url,
            is_active=session.is_active,
            started_at=session.started_at.isoformat() if session.started_at else None,
            stopped_at=session.stopped_at.isoformat() if session.stopped_at else None,
            error_message=session.error_message,
        )


class CaptureControlDTO(BaseModel):
    """캡처 제어 응답 DTO"""
    message: str
    status: CaptureStatusDTO


class FrameDTO(BaseModel):
    """프레임 응답 DTO"""
    image: str
    format: str
    encoding: str


class CaptureStartRequestDTO(BaseModel):
    """캡처 시작 요청 DTO"""
    rtsp_url: Optional[str] = None