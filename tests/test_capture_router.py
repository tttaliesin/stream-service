from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from stream_service.domain.models.capture_session import CaptureSession, CaptureStatus
from stream_service.infrastructure.adapters.input.capture_router import router
from stream_service.infrastructure.config.container import Container


@pytest.fixture
def mock_capture_use_cases():
    """Mock CaptureUseCases"""
    mock = AsyncMock()
    # get_capture_status는 동기 함수이므로 MagicMock으로 설정
    mock.get_capture_status = MagicMock()
    return mock


@pytest.fixture
def test_app(mock_capture_use_cases):
    """테스트용 FastAPI 앱"""
    from fastapi import FastAPI
    from dependency_injector import providers
    
    app = FastAPI()
    
    # Container 설정
    container = Container()
    
    # capture_use_cases를 mock으로 오버라이드
    container.capture_use_cases.override(providers.Object(mock_capture_use_cases))
    
    # 와이어링
    container.wire(modules=["stream_service.infrastructure.adapters.input.capture_router"])
    
    app.container = container
    app.include_router(router)
    
    yield app
    
    # 정리
    container.unwire()


@pytest.fixture
def client(test_app):
    """테스트 클라이언트"""
    return TestClient(test_app)


@pytest.fixture
def sample_session():
    """샘플 캡처 세션"""
    session = CaptureSession.create("rtsp://test.url")
    session.started_at = datetime(2024, 1, 1, 12, 0, 0)
    return session


class TestCaptureRouter:
    
    def test_start_capture_success(self, client, mock_capture_use_cases, sample_session):
        """캡처 시작 성공 테스트"""
        # Arrange
        sample_session.status = CaptureStatus.RUNNING
        mock_capture_use_cases.start_capture.return_value = sample_session
        
        # Act
        response = client.post("/api/capture/start")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Capture started successfully"
        assert data["status"]["status"] == "running"
        assert data["status"]["rtsp_url"] == "rtsp://test.url"
        assert data["status"]["is_active"] is True
        mock_capture_use_cases.start_capture.assert_called_once()
    
    def test_start_capture_validation_error(self, client, mock_capture_use_cases):
        """캡처 시작 검증 에러 테스트"""
        # Arrange
        mock_capture_use_cases.start_capture.side_effect = ValueError("Capture is already running")
        
        # Act
        response = client.post("/api/capture/start")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Capture is already running" in data["detail"]
    
    def test_start_capture_server_error(self, client, mock_capture_use_cases):
        """캡처 시작 서버 에러 테스트"""
        # Arrange
        mock_capture_use_cases.start_capture.side_effect = Exception("RTSP connection failed")
        
        # Act
        response = client.post("/api/capture/start")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Failed to start capture" in data["detail"]
        assert "RTSP connection failed" in data["detail"]
    
    def test_stop_capture_success(self, client, mock_capture_use_cases, sample_session):
        """캡처 중지 성공 테스트"""
        # Arrange
        sample_session.status = CaptureStatus.STOPPED
        sample_session.stopped_at = datetime(2024, 1, 1, 12, 30, 0)
        mock_capture_use_cases.stop_capture.return_value = sample_session
        
        # Act
        response = client.post("/api/capture/stop")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Capture stopped successfully"
        assert data["status"]["status"] == "stopped"
        assert data["status"]["is_active"] is False
        mock_capture_use_cases.stop_capture.assert_called_once()
    
    def test_stop_capture_validation_error(self, client, mock_capture_use_cases):
        """캡처 중지 검증 에러 테스트"""
        # Arrange
        mock_capture_use_cases.stop_capture.side_effect = ValueError("Capture is not running")
        
        # Act
        response = client.post("/api/capture/stop")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Capture is not running" in data["detail"]
    
    def test_get_capture_status(self, client, mock_capture_use_cases, sample_session):
        """캡처 상태 조회 테스트"""
        # Arrange
        sample_session.status = CaptureStatus.RUNNING
        mock_capture_use_cases.get_capture_status.return_value = sample_session
        
        # Act
        response = client.get("/api/capture/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["rtsp_url"] == "rtsp://test.url"
        assert data["is_active"] is True
        assert data["started_at"] == "2024-01-01T12:00:00"
        mock_capture_use_cases.get_capture_status.assert_called_once()
    
    def test_get_capture_status_with_error(self, client, mock_capture_use_cases, sample_session):
        """에러가 있는 캡처 상태 조회 테스트"""
        # Arrange
        sample_session.status = CaptureStatus.ERROR
        sample_session.error_message = "RTSP connection lost"
        mock_capture_use_cases.get_capture_status.return_value = sample_session
        
        # Act
        response = client.get("/api/capture/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["error_message"] == "RTSP connection lost"
        assert data["is_active"] is False
    
    def test_get_current_frame_success(self, client, mock_capture_use_cases):
        """현재 프레임 조회 성공 테스트"""
        # Arrange
        mock_frame_data = b"base64_encoded_frame_data"
        mock_capture_use_cases.get_current_frame.return_value = mock_frame_data
        
        # Act
        response = client.get("/api/capture/frame")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["image"] == mock_frame_data.decode('utf-8')
        assert data["format"] == "jpeg"
        assert data["encoding"] == "base64"
        mock_capture_use_cases.get_current_frame.assert_called_once()
    
    def test_get_current_frame_no_frame(self, client, mock_capture_use_cases):
        """프레임이 없을 때 조회 테스트"""
        # Arrange
        mock_capture_use_cases.get_current_frame.return_value = None
        
        # Act
        response = client.get("/api/capture/frame")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "No frame available"
    
    def test_get_current_frame_error(self, client, mock_capture_use_cases):
        """프레임 조회 에러 테스트"""
        # Arrange
        mock_capture_use_cases.get_current_frame.side_effect = Exception("Frame read error")
        
        # Act & Assert
        with pytest.raises(Exception):
            response = client.get("/api/capture/frame")