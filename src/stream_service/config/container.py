import socketio
import logging
from dependency_injector import containers, providers

from stream_service.config.settings import Settings
from stream_service.config.constants import EmitEvent


from stream_service.application.usecases.video_stream_usecase import VideoStreamUseCase

from stream_service.domain.services.capture_service import CaptureService

from stream_service.adapters.outbound.external.opencv_capture_engine import OpenCVCaptureEngine
from stream_service.adapters.outbound.messaging.socketio_publisher import SocketIOPublisher
from stream_service.adapters.inbound.websocket.socketio_client import SocketIOClient


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings = Settings()
    
    # Engine.IO 로거 레벨 설정
    logging.getLogger('engineio.server').setLevel(logging.DEBUG)
    logging.getLogger('socketio.server').setLevel(logging.DEBUG)
    
    # Constants
    emit_event = providers.Factory(EmitEvent)
    
    # 도메인 서비스
    capture_service = providers.Singleton(
        CaptureService,
        rtsp_url=settings.rtsp_url
    )
    
    # adapter
    capture_engine = providers.Singleton(OpenCVCaptureEngine)
    
    sio = providers.Singleton(
        socketio.AsyncClient,
        logger=True,
        engineio_logger=False
    )
    
    event_publisher = providers.Singleton(
        SocketIOPublisher,
        sio = sio,
        emit_event=emit_event
    )

    video_stream_usecase = providers.Singleton(
        VideoStreamUseCase,
        capture_service = capture_service,
        event_publisher = event_publisher,
        capture_engine = capture_engine
    )
    
    