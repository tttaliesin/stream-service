
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Stream Service"
    debug: bool = True
    host: str = "localhost"
    port: int = 8000
    
    # Socket.IO server 설정
    socketio_server_url: str = "http://localhost:8001"
    
    # RTSP 설정
    rtsp_url: str = "rtsp://210.99.70.120:1935/live/cctv003.stream"
    
    class Config:
        env_file = ".env"


settings = Settings()