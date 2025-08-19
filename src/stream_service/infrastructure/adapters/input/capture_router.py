from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ....application.use_cases.capture_use_cases import CaptureUseCases
from ....domain.models.capture_session import CaptureSession
from ...config.container import Container


class CaptureStatusResponse(BaseModel):
    status: str
    rtsp_url: str
    is_active: bool
    started_at: Optional[str]
    stopped_at: Optional[str]
    error_message: Optional[str]

    @classmethod
    def from_domain(cls, session: CaptureSession) -> "CaptureStatusResponse":
        return cls(
            status=session.status.value,
            rtsp_url=session.rtsp_url,
            is_active=session.is_active,
            started_at=session.started_at.isoformat() if session.started_at else None,
            stopped_at=session.stopped_at.isoformat() if session.stopped_at else None,
            error_message=session.error_message,
        )


class CaptureControlResponse(BaseModel):
    message: str
    status: CaptureStatusResponse


router = APIRouter(prefix="/api/capture", tags=["capture"])


@router.post("/start", response_model=CaptureControlResponse)
@inject
async def start_capture(
    capture_use_cases: CaptureUseCases = Depends(Provide[Container.capture_use_cases]),
):
    """RTSP 캡처 시작"""
    try:
        session = await capture_use_cases.start_capture()
        return CaptureControlResponse(
            message="Capture started successfully",
            status=CaptureStatusResponse.from_domain(session),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start capture: {str(e)}")


@router.post("/stop", response_model=CaptureControlResponse)
@inject
async def stop_capture(
    capture_use_cases: CaptureUseCases = Depends(Provide[Container.capture_use_cases]),
):
    """RTSP 캡처 중지"""
    try:
        session = await capture_use_cases.stop_capture()
        return CaptureControlResponse(
            message="Capture stopped successfully",
            status=CaptureStatusResponse.from_domain(session),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop capture: {str(e)}")


@router.get("/status", response_model=CaptureStatusResponse)
@inject
async def get_capture_status(
    capture_use_cases: CaptureUseCases = Depends(Provide[Container.capture_use_cases]),
):
    """현재 캡처 상태 조회"""
    session = capture_use_cases.get_capture_status()
    return CaptureStatusResponse.from_domain(session)


@router.get("/frame")
@inject
async def get_current_frame(
    capture_use_cases: CaptureUseCases = Depends(Provide[Container.capture_use_cases]),
):
    """현재 프레임 조회 (Base64 인코딩된 JPEG)"""
    frame_data = await capture_use_cases.get_current_frame()
    
    if frame_data is None:
        raise HTTPException(status_code=404, detail="No frame available")
    
    return {
        "image": frame_data.decode('utf-8'),
        "format": "jpeg",
        "encoding": "base64"
    }