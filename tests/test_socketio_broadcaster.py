import pytest
from unittest.mock import AsyncMock, MagicMock

from stream_service.infrastructure.adapters.output.socketio_broadcaster import SocketIOBroadcasterImpl


@pytest.fixture
def mock_socketio():
    """Mock socketio.AsyncServer"""
    mock_sio = AsyncMock()
    mock_sio.emit = AsyncMock()
    return mock_sio


@pytest.fixture
def broadcaster(mock_socketio):
    """SocketIOBroadcasterImpl 인스턴스"""
    return SocketIOBroadcasterImpl(mock_socketio)


class TestSocketIOBroadcasterImpl:
    
    def test_initial_state(self, broadcaster):
        """초기 상태 테스트"""
        assert broadcaster.get_connected_count() == 0
        assert not broadcaster.is_any_connected()
    
    def test_add_client(self, broadcaster):
        """클라이언트 추가 테스트"""
        # Act
        broadcaster.add_client("client1")
        broadcaster.add_client("client2")
        
        # Assert
        assert broadcaster.get_connected_count() == 2
        assert broadcaster.is_any_connected()
    
    def test_remove_client(self, broadcaster):
        """클라이언트 제거 테스트"""
        # Arrange
        broadcaster.add_client("client1")
        broadcaster.add_client("client2")
        
        # Act
        broadcaster.remove_client("client1")
        
        # Assert
        assert broadcaster.get_connected_count() == 1
        assert broadcaster.is_any_connected()
    
    def test_remove_nonexistent_client(self, broadcaster):
        """존재하지 않는 클라이언트 제거 테스트"""
        # Arrange
        broadcaster.add_client("client1")
        
        # Act - 존재하지 않는 클라이언트 제거
        broadcaster.remove_client("nonexistent")
        
        # Assert - 기존 클라이언트는 그대로
        assert broadcaster.get_connected_count() == 1
    
    def test_add_duplicate_client(self, broadcaster):
        """중복 클라이언트 추가 테스트"""
        # Act - 같은 클라이언트 두 번 추가
        broadcaster.add_client("client1")
        broadcaster.add_client("client1")
        
        # Assert - Set이므로 중복 제거됨
        assert broadcaster.get_connected_count() == 1
    
    @pytest.mark.asyncio
    async def test_broadcast_status_with_clients(self, broadcaster, mock_socketio):
        """클라이언트가 있을 때 상태 브로드캐스트 테스트"""
        # Arrange
        broadcaster.add_client("client1")
        status_data = {"status": "running", "is_active": True}
        
        # Act
        await broadcaster.broadcast_status(status_data)
        
        # Assert
        mock_socketio.emit.assert_called_once_with('capture_status', status_data)
    
    @pytest.mark.asyncio
    async def test_broadcast_status_no_clients(self, broadcaster, mock_socketio):
        """클라이언트가 없을 때 상태 브로드캐스트 테스트"""
        # Arrange
        status_data = {"status": "running", "is_active": True}
        
        # Act
        await broadcaster.broadcast_status(status_data)
        
        # Assert - 클라이언트가 없으면 emit 호출 안됨
        mock_socketio.emit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_status_error(self, broadcaster, mock_socketio):
        """상태 브로드캐스트 에러 테스트"""
        # Arrange
        broadcaster.add_client("client1")
        status_data = {"status": "running", "is_active": True}
        mock_socketio.emit.side_effect = Exception("Socket error")
        
        # Act - 에러 발생해도 예외 전파 안됨
        await broadcaster.broadcast_status(status_data)
        
        # Assert
        mock_socketio.emit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_frame_with_clients(self, broadcaster, mock_socketio):
        """클라이언트가 있을 때 프레임 브로드캐스트 테스트"""
        # Arrange
        broadcaster.add_client("client1")
        frame_data = b"base64_encoded_frame_data"
        
        # Act
        await broadcaster.broadcast_frame(frame_data)
        
        # Assert
        expected_data = {'image': frame_data.decode('utf-8')}
        mock_socketio.emit.assert_called_once_with('frame_data', expected_data)
    
    @pytest.mark.asyncio
    async def test_broadcast_frame_no_clients(self, broadcaster, mock_socketio):
        """클라이언트가 없을 때 프레임 브로드캐스트 테스트"""
        # Arrange
        frame_data = b"base64_encoded_frame_data"
        
        # Act
        await broadcaster.broadcast_frame(frame_data)
        
        # Assert - 클라이언트가 없으면 emit 호출 안됨
        mock_socketio.emit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_broadcast_frame_decode_error(self, broadcaster, mock_socketio):
        """프레임 디코딩 에러 테스트"""
        # Arrange
        broadcaster.add_client("client1")
        # 잘못된 UTF-8 바이트
        frame_data = b'\xff\xfe\x00\x00'
        
        # Act - 디코딩 에러 발생해도 예외 전파 안됨
        await broadcaster.broadcast_frame(frame_data)
        
        # Assert - emit이 호출되지 않음 (에러로 인해)
        mock_socketio.emit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_emit_to_client(self, broadcaster, mock_socketio):
        """특정 클라이언트에게 이벤트 전송 테스트"""
        # Arrange
        sid = "client1"
        event = "test_event"
        data = {"message": "test"}
        
        # Act
        await broadcaster.emit_to_client(sid, event, data)
        
        # Assert
        mock_socketio.emit.assert_called_once_with(event, data, room=sid)
    
    @pytest.mark.asyncio
    async def test_emit_to_client_error(self, broadcaster, mock_socketio):
        """특정 클라이언트 전송 에러 테스트"""
        # Arrange
        sid = "client1"
        event = "test_event"
        data = {"message": "test"}
        mock_socketio.emit.side_effect = Exception("Socket error")
        
        # Act - 에러 발생해도 예외 전파 안됨
        await broadcaster.emit_to_client(sid, event, data)
        
        # Assert
        mock_socketio.emit.assert_called_once_with(event, data, room=sid)