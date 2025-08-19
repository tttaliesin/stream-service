import socketio
from dependency_injector import containers, providers

from ...application.use_cases.capture_use_cases import CaptureUseCases
from ...domain.services.capture_service import CaptureService
from ..adapters.output.opencv_capture_engine import OpenCVCaptureEngine
from ..adapters.output.socketio_broadcaster import SocketIOBroadcasterImpl


class Container(containers.DeclarativeContainer):
    # Socket.IO 서버 인스턴스
    socketio_server = providers.Singleton(
        socketio.AsyncServer,
        cors_allowed_origins="*",
        async_mode="asgi",
    )
    
    # RTSP 캡처 엔진
    capture_engine = providers.Singleton(OpenCVCaptureEngine)
    
    # Socket.IO 브로드캐스터
    socketio_broadcaster = providers.Factory(
        SocketIOBroadcasterImpl,
        sio=socketio_server,
    )
    
    # 캡처 서비스
    capture_service = providers.Factory(
        CaptureService,
        capture_engine=capture_engine,
        socketio_broadcaster=socketio_broadcaster,
    )
    
    # 캡처 유스케이스
    capture_use_cases = providers.Factory(
        CaptureUseCases,
        capture_service=capture_service,
    )