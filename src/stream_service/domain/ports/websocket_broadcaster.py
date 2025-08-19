from abc import ABC, abstractmethod
from typing import Any, Dict


class SocketIOBroadcaster(ABC):
    @abstractmethod
    async def broadcast_status(self, status: Dict[str, Any]) -> None:
        """캡처 상태를 모든 연결된 클라이언트에게 브로드캐스트"""
        pass
    
    @abstractmethod
    async def broadcast_frame(self, frame_data: bytes) -> None:
        """프레임 데이터를 모든 연결된 클라이언트에게 브로드캐스트"""
        pass
    
    @abstractmethod
    async def emit_to_client(self, sid: str, event: str, data: Any) -> None:
        """특정 클라이언트에게 이벤트 전송"""
        pass