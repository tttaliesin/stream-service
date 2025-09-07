
import logging
import socketio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stream_service.config.settings import settings
from stream_service.config.container import Container

from stream_service.adapters.inbound.http.static_router import router
from stream_service.adapters.inbound.websocket.socketio_client import SocketIOClient

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    container = app.container
    socketio_client = SocketIOClient(
        sio=container.sio(),
        event_subscriber=container.video_stream_usecase()
    )
    socketio_client.resister_event()
    await container.sio().connect(settings.socketio_server_url)
    
    yield
    
    # Shutdown
    await container.sio().disconnect()

def create_app() -> FastAPI:
    # DI Container 초기화
    container = Container()
    
    # FastAPI 앱 생성
    app = FastAPI(
        title="RTSP Stream Service",
        version="0.1.0",
        description="Real-time RTSP stream capture and broadcast service",
        lifespan=lifespan
    )    
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.container = container
    app.include_router(router)
    
    return app

import asyncio

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import signal
    
    def signal_handler(signum, frame):
        print("Shutting down gracefully...")
        
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        uvicorn.run(app, host=settings.host, port=settings.port)
    except KeyboardInterrupt:
        print("Server stopped.")    
