
import logging
import asyncio
from fastapi import FastAPI


from config.settings import settings
from config.container import Container

from adapters.inbound.http.static_router import router as static_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def create_app() -> FastAPI:
    # DI Container 초기화
    container = Container()
    
    # FastAPI 앱 생성
    app = FastAPI(
        title="RTSP Stream Service",
        version="0.1.0",
        description="Real-time RTSP stream capture and broadcast service"
    )
    # app.container = container
    
    app.include_router(static_router)
    
    stream_messaging = container.stream_messaging()
    
    try:
        await stream_messaging.connect()
        logger.info("Socket.io adapter connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect Socket.io adapter: {e}")
        raise
    
    
    container.socketio_command_adapter()
    logger.info("Socket.io command adapter initialized")
    
    return app

async def main():
    return await create_app()

app = asyncio.run(main())

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
