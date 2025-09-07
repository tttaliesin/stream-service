from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel

class ResponseClientMetadataDTO(BaseModel):
    client_type: str
    
class VideoFrameFromServiceDTO(BaseModel):
    frame_data: bytes
    
class CaptureStatusResponseDTO(BaseModel):
    rtsp_url: str
    status: str
    is_active: bool