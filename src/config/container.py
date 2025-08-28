from dependency_injector import containers, providers

from application.usecases.capture_stream_handler import CaptureStreamHandler

from domain.services.capture_service import CaptureService

from adapters.outbound.external.opencv_capture_engine import OpenCVCaptureEngine
from adapters.outbound.messaging.socketio_streaming_adapter import SocketIOStreamingAdapter
from adapters.inbound.websocket.socketio_command_adapter import SocketIOCommandAdapter

from config.settings import settings


class Container(containers.DeclarativeContainer):
    """의존성 주입 컨테이너"""
    
    # 설정
    config = providers.Configuration()
    rtsp_url = providers.Object(settings.rtsp_url)
    socketio_server_url = providers.Object(settings.socketio_server_url)
    
    # Outbound adapters
    capture_engine = providers.Singleton(OpenCVCaptureEngine)
    
    stream_messaging = providers.Singleton(
        SocketIOStreamingAdapter,
        socketio_url=socketio_server_url
    )
    
    # event_logger는 stream_messaging과 같은 인스턴스 사용
    event_logger = stream_messaging
    
    # 도메인 서비스
    capture_service = providers.Singleton(
        CaptureService,
        capture_engine=capture_engine,
        rtsp_url=rtsp_url
    )
    
    # 애플리케이션 서비스 (Stream Handler)
    capture_stream_handler = providers.Singleton(
        CaptureStreamHandler,
        capture_service=capture_service,
        stream_messaging=stream_messaging,
        event_logger=event_logger
    )
    
    # Inbound adapters
    socketio_command_adapter = providers.Singleton(
        SocketIOCommandAdapter,
        stream_handler=capture_stream_handler,
        socketio_adapter=stream_messaging
    )