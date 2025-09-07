import asyncio
import base64
import logging
from typing import AsyncGenerator, Optional

import cv2

from stream_service.application.ports.outbound.capture_engine import CaptureEngine

logger = logging.getLogger(__name__)


class OpenCVCaptureEngine(CaptureEngine):
    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_capturing = False
        self._frame_rate = 30  # FPS
        self._frame_interval = 1.0 / self._frame_rate
        
        # 타임아웃 및 재시도 설정
        self._connection_timeout = 10000  # ms
        self._read_timeout = 5000  # ms
        self._max_retries = 3
        self._retry_delay = 2.0  # seconds
        self._consecutive_failures = 0
        self._max_consecutive_failures = 10
    
    async def start_capture(self, rtsp_url: str) -> None:
        """RTSP 스트림 캡처 시작"""
        if self._is_capturing:
            raise RuntimeError("Capture is already running")
        
        logger.info(f"Starting RTSP capture from {rtsp_url}")
        
        # 캡처 시작 플래그 설정 (재시도 루프에서 사용)
        self._is_capturing = True
        
        # OpenCV VideoCapture는 동기 작업이므로 executor에서 실행
        loop = asyncio.get_event_loop()
        
        def _open_capture():
            attempt = 0
            while self._is_capturing:  # 캡처가 중지될 때까지 무한 재시도
                attempt += 1
                try:
                    logger.info(f"RTSP 연결 시도 {attempt}: {rtsp_url}")
                    
                    cap = cv2.VideoCapture(rtsp_url)
                    
                    # 타임아웃 설정
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self._connection_timeout)
                    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self._read_timeout)
                    
                    # RTSP 스트림 설정 최적화
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기 최소화
                    cap.set(cv2.CAP_PROP_FPS, self._frame_rate)
                    
                    # 추가 RTSP 설정
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
                    
                    if not cap.isOpened():
                        cap.release()
                        if self._is_capturing:  # 여전히 캡처 중이면 재시도
                            logger.warning(f"연결 실패, {self._retry_delay}초 후 재시도...")
                            import time
                            time.sleep(self._retry_delay)
                            continue
                        else:
                            raise RuntimeError("Capture cancelled during connection")
                    
                    # 연결 성공 후 실제 프레임 읽기 테스트
                    ret, test_frame = cap.read()
                    if not ret or test_frame is None:
                        cap.release()
                        if self._is_capturing:  # 여전히 캡처 중이면 재시도
                            logger.warning(f"프레임 읽기 실패, {self._retry_delay}초 후 재시도...")
                            import time
                            time.sleep(self._retry_delay)
                            continue
                        else:
                            raise RuntimeError("Capture cancelled during frame test")
                    
                    logger.info(f"RTSP 연결 성공! (시도 {attempt}회) 프레임 크기: {test_frame.shape if test_frame is not None else 'Unknown'}")
                    self._consecutive_failures = 0
                    return cap
                    
                except Exception as e:
                    logger.error(f"연결 시도 {attempt} 실패: {e}")
                    if self._is_capturing:  # 여전히 캡처 중이면 재시도
                        logger.info(f"{self._retry_delay}초 후 재시도...")
                        import time
                        time.sleep(self._retry_delay)
                        continue
                    else:
                        raise RuntimeError("Capture cancelled during retry")
            
            raise RuntimeError("Capture was cancelled")
        
        try:
            self._cap = await loop.run_in_executor(None, _open_capture)
            # _is_capturing은 이미 True로 설정됨
            logger.info("RTSP capture started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start RTSP capture: {e}")
            self._cleanup()
            raise
    
    async def stop_capture(self) -> None:
        """RTSP 스트림 캡처 중지"""
        if not self._is_capturing:
            return
        
        logger.info("Stopping RTSP capture")
        self._cleanup()
        logger.info("RTSP capture stopped")
    
    async def get_current_frame(self) -> Optional[bytes]:
        """현재 프레임을 JPEG 바이너리로 반환"""
        if not self._is_capturing or not self._cap:
            return None
        
        loop = asyncio.get_event_loop()
        
        def _read_frame():
            if not self._cap or not self._cap.isOpened():
                logger.warning("VideoCapture가 열려있지 않음")
                return None
                
            ret, frame = self._cap.read()
            if not ret or frame is None:
                self._consecutive_failures += 1
                logger.warning(f"프레임 읽기 실패 (연속 실패: {self._consecutive_failures})")
                
                # 연속 실패가 많으면 연결 상태 재확인
                if self._consecutive_failures >= self._max_consecutive_failures:
                    logger.error(f"연속 {self._max_consecutive_failures}회 실패, 스트림 연결 문제로 판단")
                    return None
                
                return None
            
            # 성공 시 연속 실패 카운터 리셋
            if self._consecutive_failures > 0:
                logger.info(f"프레임 읽기 복구됨 (이전 연속 실패: {self._consecutive_failures}회)")
                self._consecutive_failures = 0
            
            # 프레임을 JPEG로 인코딩
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not success:
                logger.warning("JPEG 인코딩 실패")
                return None
            
            return buffer.tobytes()
        
        try:
            return await loop.run_in_executor(None, _read_frame)
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None
    
    def is_capturing(self) -> bool:
        """현재 캡처 중인지 확인"""
        return self._is_capturing
    
    async def frame_stream(self) -> AsyncGenerator[bytes, None]:
        """실시간 프레임 스트림"""
        if not self._is_capturing:
            logger.warning("Cannot start frame stream: capture is not running")
            return
        
        logger.info("Starting frame stream")
        
        while self._is_capturing and self._cap:
            try:
                frame_data = await self.get_current_frame()
                
                if frame_data:
                    # frame_data는 이미 JPEG 바이너리
                    yield frame_data
                    
                    # 프레임 레이트 제어
                    await asyncio.sleep(self._frame_interval)
                else:
                    # 프레임 없을 때는 좀 더 대기
                    await asyncio.sleep(0.1)
                    
                    # 연속 실패가 너무 많으면 스트림 중지 고려
                    if self._consecutive_failures >= self._max_consecutive_failures:
                        logger.error("프레임 스트림 연속 실패로 인한 스트림 중지")
                        break
                
            except asyncio.CancelledError:
                logger.info("Frame stream cancelled")
                break
            except Exception as e:
                logger.error(f"Error in frame stream: {e}")
                await asyncio.sleep(1)  # 에러 시 잠시 대기
        
        logger.info("Frame stream ended")
    
    def _cleanup(self) -> None:
        """리소스 정리"""
        self._is_capturing = False
        
        if self._cap:
            try:
                self._cap.release()
            except Exception as e:
                logger.error(f"Error releasing capture: {e}")
            finally:
                self._cap = None
    
    def __del__(self):
        """소멸자에서 리소스 정리"""
        self._cleanup()