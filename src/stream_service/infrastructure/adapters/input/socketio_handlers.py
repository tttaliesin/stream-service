import logging

import socketio

from ....application.use_cases.capture_use_cases import CaptureUseCases
from ..output.socketio_broadcaster import SocketIOBroadcasterImpl

logger = logging.getLogger(__name__)


def setup_socketio_handlers(
    sio: socketio.AsyncServer,
    capture_use_cases: CaptureUseCases,
    broadcaster: SocketIOBroadcasterImpl,
):
    """Socket.IO 이벤트 핸들러 설정"""

    @sio.event
    async def connect(sid, environ):
        """클라이언트 연결"""
        logger.info(f"Client {sid} connected")
        broadcaster.add_client(sid)
        
        # 현재 캡처 상태를 새 클라이언트에게 전송
        try:
            current_status = capture_use_cases.get_capture_status()
            status_data = {
                "status": current_status.status.value,
                "rtsp_url": current_status.rtsp_url,
                "is_active": current_status.is_active,
                "started_at": current_status.started_at.isoformat() if current_status.started_at else None,
                "stopped_at": current_status.stopped_at.isoformat() if current_status.stopped_at else None,
                "error_message": current_status.error_message,
            }
            await broadcaster.emit_to_client(sid, 'capture_status', status_data)
        except Exception as e:
            logger.error(f"Error sending initial status to {sid}: {e}")

    @sio.event
    async def disconnect(sid):
        """클라이언트 연결 해제"""
        logger.info(f"Client {sid} disconnected")
        broadcaster.remove_client(sid)

    @sio.event
    async def start_capture(sid):
        """캡처 시작 요청"""
        logger.info(f"Client {sid} requested to start capture")
        try:
            session = await capture_use_cases.start_capture()
            await broadcaster.emit_to_client(
                sid,
                'capture_control_response',
                {
                    "success": True,
                    "message": "Capture started successfully",
                    "status": session.status.value
                }
            )
        except ValueError as e:
            await broadcaster.emit_to_client(
                sid,
                'capture_control_response',
                {
                    "success": False,
                    "message": str(e),
                    "error_type": "validation_error"
                }
            )
        except Exception as e:
            logger.error(f"Error starting capture for {sid}: {e}")
            await broadcaster.emit_to_client(
                sid,
                'capture_control_response',
                {
                    "success": False,
                    "message": f"Failed to start capture: {str(e)}",
                    "error_type": "server_error"
                }
            )

    @sio.event
    async def stop_capture(sid):
        """캡처 중지 요청"""
        logger.info(f"Client {sid} requested to stop capture")
        try:
            session = await capture_use_cases.stop_capture()
            await broadcaster.emit_to_client(
                sid,
                'capture_control_response',
                {
                    "success": True,
                    "message": "Capture stopped successfully",
                    "status": session.status.value
                }
            )
        except ValueError as e:
            await broadcaster.emit_to_client(
                sid,
                'capture_control_response',
                {
                    "success": False,
                    "message": str(e),
                    "error_type": "validation_error"
                }
            )
        except Exception as e:
            logger.error(f"Error stopping capture for {sid}: {e}")
            await broadcaster.emit_to_client(
                sid,
                'capture_control_response',
                {
                    "success": False,
                    "message": f"Failed to stop capture: {str(e)}",
                    "error_type": "server_error"
                }
            )

    @sio.event
    async def get_status(sid):
        """현재 상태 요청"""
        logger.debug(f"Client {sid} requested current status")
        try:
            current_status = capture_use_cases.get_capture_status()
            status_data = {
                "status": current_status.status.value,
                "rtsp_url": current_status.rtsp_url,
                "is_active": current_status.is_active,
                "started_at": current_status.started_at.isoformat() if current_status.started_at else None,
                "stopped_at": current_status.stopped_at.isoformat() if current_status.stopped_at else None,
                "error_message": current_status.error_message,
            }
            await broadcaster.emit_to_client(sid, 'capture_status', status_data)
        except Exception as e:
            logger.error(f"Error getting status for {sid}: {e}")
            await broadcaster.emit_to_client(
                sid,
                'error',
                {
                    "message": f"Failed to get status: {str(e)}",
                    "error_type": "server_error"
                }
            )

    @sio.event
    async def request_frame(sid):
        """현재 프레임 요청"""
        logger.debug(f"Client {sid} requested current frame")
        try:
            frame_data = await capture_use_cases.get_current_frame()
            if frame_data:
                frame_str = frame_data.decode('utf-8')
                await broadcaster.emit_to_client(sid, 'frame_data', {'image': frame_str})
            else:
                await broadcaster.emit_to_client(
                    sid,
                    'error',
                    {
                        "message": "No frame available",
                        "error_type": "no_data"
                    }
                )
        except Exception as e:
            logger.error(f"Error getting frame for {sid}: {e}")
            await broadcaster.emit_to_client(
                sid,
                'error',
                {
                    "message": f"Failed to get frame: {str(e)}",
                    "error_type": "server_error"
                }
            )

    logger.info("Socket.IO event handlers configured")