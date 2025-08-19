import socketio
from fastapi import FastAPI

from stream_service.infrastructure.adapters.input.capture_router import router as capture_router
from stream_service.infrastructure.adapters.input.socketio_handlers import setup_socketio_handlers
from stream_service.infrastructure.config.container import Container


def create_app() -> FastAPI:
    # DI Container 초기화
    container = Container()
    container.wire(modules=[
        "stream_service.infrastructure.adapters.input.capture_router",
    ])
    
    # FastAPI 앱 생성
    app = FastAPI(
        title="RTSP Stream Service",
        version="0.1.0",
        description="Real-time RTSP stream capture and broadcast service"
    )
    app.container = container
    
    # REST API 라우터 추가
    app.include_router(capture_router)
    
    # Socket.IO 서버 설정
    sio = container.socketio_server()
    socketio_broadcaster = container.socketio_broadcaster()
    capture_use_cases = container.capture_use_cases()
    
    # Socket.IO 이벤트 핸들러 설정
    setup_socketio_handlers(sio, capture_use_cases, socketio_broadcaster)
    
    # Socket.IO ASGI 앱 생성
    socketio_asgi_app = socketio.ASGIApp(sio, app)
    
    return socketio_asgi_app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
