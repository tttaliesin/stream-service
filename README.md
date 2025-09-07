# Stream Service

실시간 RTSP 비디오 스트림을 캡처하고 Socket.IO를 통해 브로드캐스트하는 서비스

## 개요

Stream Service는 RTSP 스트림을 캡처하여 Socket.IO 서버로 전송하는 마이크로서비스입니다. Event Management Service와 연동하여 클라이언트의 캡처 요청을 처리하고, 실시간 비디오 프레임을 전송합니다. 헥사고날 아키텍처를 적용하여 외부 의존성과 비즈니스 로직을 분리했습니다.

## 주요 기능

- **RTSP 스트림 캡처**: OpenCV를 사용한 실시간 RTSP 스트림 처리
- **Socket.IO 통신**: Event Management Service와의 실시간 양방향 통신
- **비디오 프레임 전송**: 캡처된 비디오 프레임을 Socket.IO 서버로 실시간 전송
- **캡처 상태 관리**: 캡처 세션의 상태를 추적하고 상태 조회 API 제공
- **명령 처리**: 원격 캡처 시작/중지 명령 수신 및 처리
- **에러 핸들링**: 연결 실패, 스트림 오류 등에 대한 견고한 에러 처리

## 아키텍처

### 헥사고날 아키텍처 구조
```
├── src/
│   ├── domain/                    # 도메인 계층
│   │   ├── model/                # 도메인 모델
│   │   │   └── capture_session.py
│   │   └── services/             # 도메인 서비스
│   │       └── capture_service.py
│   ├── application/              # 애플리케이션 계층
│   │   ├── ports/                # 포트 (인터페이스)
│   │   │   ├── inbound/          # 인바운드 포트
│   │   │   └── outbound/         # 아웃바운드 포트
│   │   ├── usecases/             # 유스케이스
│   │   │   └── capture_stream_handler.py
│   │   └── dto/                  # 데이터 전송 객체
│   │       └── capture_dto.py
│   ├── adapters/                 # 어댑터 계층
│   │   ├── inbound/              # 인바운드 어댑터
│   │   │   ├── http/             # REST API
│   │   │   └── websocket/        # Socket.IO 명령 수신
│   │   └── outbound/             # 아웃바운드 어댑터
│   │       ├── external/         # 외부 시스템 (OpenCV)
│   │       └── messaging/        # Socket.IO 클라이언트
│   └── config/                   # 설정 및 의존성 주입
```

## 설치 및 실행

### 요구사항
- Python 3.11+
- OpenCV 4.x
- UV 패키지 매니저
- RTSP 스트림 소스 (IP 카메라 등)

### 환경 설정
1. 환경 변수 설정
```bash
# .env 파일 생성
RTSP_URL=rtsp://your-camera-ip:port/stream
SOCKETIO_SERVER_URL=http://localhost:8001
DEBUG=true
```

2. 의존성 설치
```bash
uv sync
```

### 실행
```bash
# 개발 서버 실행
uv run src/main.py

# 또는 uvicorn으로 실행
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 문서

### Socket.IO 이벤트 (수신)

Event Management Service로부터 수신하는 이벤트:

| 이벤트명 | 설명 | 데이터 형식 |
|---------|------|------------|
| `capture_start_request` | 캡처 시작 요청 | `{client_id: string, metadata?: object}` |
| `capture_stop_request` | 캡처 중지 요청 | `{client_id: string, metadata?: object}` |
| `capture_status_request` | 캡처 상태 조회 요청 | `{requesting_client: string}` |

### Socket.IO 이벤트 (발신)

Event Management Service로 전송하는 이벤트:

| 이벤트명 | 설명 | 데이터 형식 |
|---------|------|------------|
| `video_frame_from_service` | 비디오 프레임 전송 | `VideoFrameFromServiceDTO` |
| `capture_status_response` | 캡처 상태 응답 | `CaptureStatusResponseDTO` |

### REST API

#### 정적 파일 서빙

| 메서드 | 엔드포인트 | 설명 |
|-------|------------|------|
| GET | `/` | 기본 HTML 페이지 |
| GET | `/static/{filename}` | 정적 파일 제공 |

#### 상태 확인

| 메서드 | 엔드포인트 | 설명 | 응답 |
|-------|------------|------|------|
| GET | `/health` | 서비스 상태 확인 | `{"status": "ok"}` |

## 데이터 모델

### CaptureSession (도메인 모델)
```python
class CaptureSession:
    is_active: bool          # 캡처 활성 상태
    rtsp_url: str           # RTSP 스트림 URL
    error_message: str      # 에러 메시지 (있는 경우)
    frame_callback: callable # 프레임 콜백 함수
```

### CaptureStatusDTO
```python
{
    "is_active": "boolean",
    "rtsp_url": "string",
    "error_message": "string (optional)"
}
```

### VideoFrameFromServiceDTO
```python
{
    "frame_data": "bytes",
    "metadata": "dict (optional)"
}
```

## 주요 컴포넌트

### 1. CaptureService (도메인 서비스)
- RTSP 스트림 캡처 로직 관리
- 캡처 세션 상태 추적
- 프레임 콜백 처리

### 2. SocketIOClient (인바운드 어댑터)
- Event Management Service로부터 명령 수신
- 이벤트를 도메인 로직으로 전달

### 3. SocketIOPublisher (아웃바운드 어댑터)
- Event Management Service로 비디오 프레임 전송
- 연결 관리 및 에러 처리

### 4. OpenCVCaptureEngine (외부 어댑터)
- OpenCV를 사용한 실제 RTSP 스트림 캡처
- 비동기 프레임 처리

## 동작 플로우

### 캡처 시작 플로우
1. Event Management Service에서 `capture_start_request` 수신
2. `CaptureEventSubscriber`가 요청 처리
3. `CaptureService`가 RTSP 캡처 시작
4. `OpenCVCaptureEngine`이 실제 스트림 캡처
5. 캡처된 프레임을 콜백으로 `SocketIOPublisher`에 전달
6. 비디오 프레임을 Event Management Service로 전송

### 캡처 중지 플로우
1. Event Management Service에서 `capture_stop_request` 수신
2. `CaptureService`가 캡처 중지
3. 리소스 정리 및 상태 업데이트

### 상태 조회 플로우
1. Event Management Service에서 `capture_status_request` 수신
2. 현재 캡처 상태를 DTO로 변환
3. `capture_status_response`로 상태 응답 전송

## 설정

### config/settings.py
```python
class Settings:
    rtsp_url: str = "rtsp://localhost:8554/stream"
    socketio_server_url: str = "http://localhost:8001"
    debug: bool = False
    
    # OpenCV 설정
    capture_buffer_size: int = 1
    capture_timeout: int = 5000
    
    # Socket.IO 설정
    connection_retry_attempts: int = 3
    connection_retry_delay: int = 2
```

## 에러 처리

### RTSP 연결 실패
- 자동 재연결 시도 (최대 3회)
- 에러 상태를 Event Management Service에 알림
- 로그를 통한 디버깅 정보 제공

### Socket.IO 연결 실패
- 연결 재시도 로직
- 서비스 시작 실패 시 적절한 에러 메시지

### 프레임 처리 에러
- 개별 프레임 에러는 스트림 중단 없이 로깅만 수행
- 연속적인 에러 발생 시 캡처 중지

## 사용 예시

### 직접 RTSP 스트림 테스트
```python
from domain.services.capture_service import CaptureService
from adapters.outbound.external.opencv_capture_engine import OpenCVCaptureEngine

# 캡처 엔진 생성
engine = OpenCVCaptureEngine()
service = CaptureService(engine, "rtsp://localhost:8554/stream")

# 프레임 콜백 설정
def frame_callback(frame_data):
    print(f"Received frame: {len(frame_data)} bytes")

service.set_frame_callback(frame_callback)

# 캡처 시작
await service.start_capture()
```

### Socket.IO 클라이언트로 테스트
```javascript
const io = require('socket.io-client');

// Event Management Service에 서비스로 연결
const socket = io('http://localhost:8001?type=service');

socket.on('connect', () => {
    console.log('Connected to Event Management Service');
    
    // 캡처 시작 요청
    socket.emit('capture_start_request', {
        client_id: 'test-client',
        metadata: {}
    });
});

// 비디오 프레임 전송 시뮬레이션
setInterval(() => {
    socket.emit('video_frame_from_service', {
        frame_data: Buffer.from('fake-frame-data'),
        metadata: {timestamp: Date.now()}
    });
}, 33); // 30 FPS
```

## 개발 가이드

### 새로운 캡처 엔진 추가
1. `application/ports/outbound/capture_engine.py` 인터페이스 구현
2. `adapters/outbound/external/` 디렉토리에 새 엔진 클래스 생성
3. `config/container.py`에서 의존성 주입 설정

### 새로운 메시징 어댑터 추가
1. `application/ports/outbound/stream_messaging.py` 인터페이스 구현
2. `adapters/outbound/messaging/` 디렉토리에 새 어댑터 생성
3. 설정 파일에서 어댑터 선택 로직 추가

## 테스트

### 단위 테스트
```bash
uv run pytest

# 커버리지 확인
uv run pytest --cov=src
```

### 통합 테스트
```bash
# RTSP 서버 시뮬레이션 필요
# Event Management Service 실행 필요
uv run pytest tests/integration/
```

## 배포

### Docker 컨테이너
```dockerfile
FROM python:3.11-slim

# OpenCV 의존성 설치
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN pip install uv && uv sync

EXPOSE 8000
CMD ["uv", "run", "src/main.py"]
```

### 환경별 설정
- 개발: `.env.dev`
- 스테이징: `.env.staging`
- 프로덕션: `.env.prod`

## 모니터링

### 로그 레벨
- `DEBUG`: 프레임 처리 상세 정보
- `INFO`: 캡처 상태 변경, 연결 상태
- `WARNING`: 일시적 에러, 재시도
- `ERROR`: 심각한 에러, 서비스 중단

### 메트릭
- 초당 프레임 수 (FPS)
- Socket.IO 연결 상태
- RTSP 스트림 상태
- 메모리 사용량

## 트러블슈팅

### 일반적인 문제들

#### RTSP 연결 실패
```bash
# 네트워크 연결 확인
ping your-camera-ip

# RTSP URL 테스트
ffplay rtsp://your-camera-ip:port/stream
```

#### Socket.IO 연결 실패
```bash
# Event Management Service 상태 확인
curl http://localhost:8001/health

# 네트워크 포트 확인
netstat -an | grep 8001
```

#### 높은 메모리 사용량
- OpenCV 버퍼 크기 조정
- 프레임 처리 최적화
- 메모리 리크 확인