import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stream_service.infrastructure.adapters.output.opencv_capture_engine import OpenCVCaptureEngine


@pytest.fixture
def capture_engine():
    return OpenCVCaptureEngine()


@pytest.fixture
def mock_cv2_videocapture():
    """Mock cv2.VideoCapture"""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, b"fake_frame_data")
    mock_cap.set.return_value = True
    mock_cap.release.return_value = None
    return mock_cap


class TestOpenCVCaptureEngine:
    
    @pytest.mark.asyncio
    async def test_initial_state(self, capture_engine):
        """초기 상태 테스트"""
        assert not capture_engine.is_capturing()
        assert capture_engine._cap is None
    
    @pytest.mark.asyncio
    @patch('cv2.VideoCapture')
    @patch('cv2.imencode')
    async def test_start_capture_success(self, mock_imencode, mock_videocapture, capture_engine, mock_cv2_videocapture):
        """캡처 시작 성공 테스트"""
        # Arrange
        rtsp_url = "rtsp://210.99.70.120:1935/live/cctv006.streamd"
        mock_videocapture.return_value = mock_cv2_videocapture
        mock_imencode.return_value = (True, b"encoded_jpeg")
        
        # Act
        await capture_engine.start_capture(rtsp_url)
        
        # Assert
        assert capture_engine.is_capturing()
        mock_videocapture.assert_called_once_with(rtsp_url)
        mock_cv2_videocapture.set.assert_called()
    
    @pytest.mark.asyncio
    @patch('cv2.VideoCapture')
    async def test_start_capture_failure(self, mock_videocapture, capture_engine):
        """캡처 시작 실패 테스트"""
        # Arrange
        rtsp_url = "rtsp://invalid.url"
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_videocapture.return_value = mock_cap
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to open RTSP stream"):
            await capture_engine.start_capture(rtsp_url)
        
        assert not capture_engine.is_capturing()
    
    @pytest.mark.asyncio
    async def test_start_capture_already_running(self, capture_engine):
        """이미 실행 중일 때 캡처 시작 테스트"""
        # Arrange
        capture_engine._is_capturing = True
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Capture is already running"):
            await capture_engine.start_capture("rtsp://test.url")
    
    @pytest.mark.asyncio
    async def test_stop_capture(self, capture_engine, mock_cv2_videocapture):
        """캡처 중지 테스트"""
        # Arrange
        capture_engine._is_capturing = True
        capture_engine._cap = mock_cv2_videocapture
        
        # Act
        await capture_engine.stop_capture()
        
        # Assert
        assert not capture_engine.is_capturing()
        mock_cv2_videocapture.release.assert_called_once()
        assert capture_engine._cap is None
    
    @pytest.mark.asyncio
    async def test_stop_capture_not_running(self, capture_engine):
        """실행 중이 아닐 때 캡처 중지 테스트"""
        # Act
        await capture_engine.stop_capture()
        
        # Assert - 에러 없이 완료되어야 함
        assert not capture_engine.is_capturing()
    
    @pytest.mark.asyncio
    @patch('cv2.imencode')
    async def test_get_current_frame_success(self, mock_imencode, capture_engine, mock_cv2_videocapture):
        """현재 프레임 가져오기 성공 테스트"""
        # Arrange
        import numpy as np
        capture_engine._is_capturing = True
        capture_engine._cap = mock_cv2_videocapture
        mock_cv2_videocapture.read.return_value = (True, b"frame_data")
        mock_buffer = np.array([1, 2, 3, 4], dtype=np.uint8)  # numpy array로 모킹
        mock_imencode.return_value = (True, mock_buffer)
        
        # Act
        frame = await capture_engine.get_current_frame()
        
        # Assert
        assert frame == mock_buffer.tobytes()
        mock_cv2_videocapture.read.assert_called_once()
        mock_imencode.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_frame_not_capturing(self, capture_engine):
        """캡처하지 않을 때 현재 프레임 가져오기 테스트"""
        # Act
        frame = await capture_engine.get_current_frame()
        
        # Assert
        assert frame is None
    
    @pytest.mark.asyncio
    @patch('cv2.imencode')
    async def test_get_current_frame_read_failure(self, mock_imencode, capture_engine, mock_cv2_videocapture):
        """프레임 읽기 실패 테스트"""
        # Arrange
        capture_engine._is_capturing = True
        capture_engine._cap = mock_cv2_videocapture
        mock_cv2_videocapture.read.return_value = (False, None)
        
        # Act
        frame = await capture_engine.get_current_frame()
        
        # Assert
        assert frame is None
        mock_imencode.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('cv2.imencode')
    async def test_get_current_frame_encode_failure(self, mock_imencode, capture_engine, mock_cv2_videocapture):
        """프레임 인코딩 실패 테스트"""
        # Arrange
        capture_engine._is_capturing = True
        capture_engine._cap = mock_cv2_videocapture
        mock_cv2_videocapture.read.return_value = (True, b"frame_data")
        mock_imencode.return_value = (False, None)
        
        # Act
        frame = await capture_engine.get_current_frame()
        
        # Assert
        assert frame is None
    
    @pytest.mark.asyncio
    async def test_frame_stream_not_capturing(self, capture_engine):
        """캡처하지 않을 때 프레임 스트림 테스트"""
        # Act
        frame_generator = capture_engine.frame_stream()
        
        # Assert - 제너레이터가 즉시 종료되어야 함
        frames = []
        async for frame in frame_generator:
            frames.append(frame)
        
        assert len(frames) == 0
    
    @pytest.mark.asyncio
    @patch('cv2.imencode')
    async def test_frame_stream_success(self, mock_imencode, capture_engine, mock_cv2_videocapture):
        """프레임 스트림 성공 테스트"""
        # Arrange
        capture_engine._is_capturing = True
        capture_engine._cap = mock_cv2_videocapture
        capture_engine._frame_interval = 0.01  # 빠른 테스트를 위해
        
        mock_cv2_videocapture.read.return_value = (True, b"frame_data")
        import numpy as np
        mock_buffer = np.array([1, 2, 3, 4], dtype=np.uint8)
        mock_imencode.return_value = (True, mock_buffer)
        
        # Act - 몇 개 프레임만 가져오고 중지
        frame_generator = capture_engine.frame_stream()
        frames = []
        
        async for frame in frame_generator:
            frames.append(frame)
            if len(frames) >= 2:  # 2개 프레임만 테스트
                capture_engine._is_capturing = False
                break
        
        # Assert
        assert len(frames) == 2
        expected_frame = base64.b64encode(mock_buffer.tobytes()).decode('utf-8').encode('utf-8')
        assert all(frame == expected_frame for frame in frames)
    
    def test_cleanup(self, capture_engine, mock_cv2_videocapture):
        """리소스 정리 테스트"""
        # Arrange
        capture_engine._is_capturing = True
        capture_engine._cap = mock_cv2_videocapture
        
        # Act
        capture_engine._cleanup()
        
        # Assert
        assert not capture_engine._is_capturing
        mock_cv2_videocapture.release.assert_called_once()
        assert capture_engine._cap is None
    
    def test_cleanup_with_exception(self, capture_engine, mock_cv2_videocapture):
        """리소스 정리 중 예외 발생 테스트"""
        # Arrange
        capture_engine._is_capturing = True
        capture_engine._cap = mock_cv2_videocapture
        mock_cv2_videocapture.release.side_effect = Exception("Release error")
        
        # Act - 예외가 발생해도 정리가 완료되어야 함
        capture_engine._cleanup()
        
        # Assert
        assert not capture_engine._is_capturing
        assert capture_engine._cap is None