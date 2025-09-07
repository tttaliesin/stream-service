// Socket.IO 연결
const socket = io('http://localhost:8001', {
    query: {
        type: 'client'
    }
});

// 디버그: 모든 이벤트 수신 로그
socket.onAny((eventName, data) => {
    console.log(`Received event: ${eventName}`, data);
});

// DOM 요소들
const startCaptureBtn = document.getElementById('startCaptureBtn');
const stopCaptureBtn = document.getElementById('stopCaptureBtn');
const startStreamingBtn = document.getElementById('startStreamingBtn');
const stopStreamingBtn = document.getElementById('stopStreamingBtn');
const videoFrame = document.getElementById('videoFrame');
const videoCanvas = document.getElementById('videoCanvas');
const noVideo = document.getElementById('noVideo');
const connectionStatus = document.getElementById('connectionStatus');
const connectionText = document.getElementById('connectionText');
const captureStatus = document.getElementById('captureStatus');
const captureText = document.getElementById('captureText');
const rtspUrlEl = document.getElementById('rtspUrl');

// Canvas 컨텍스트
const ctx = videoCanvas.getContext('2d');

// 상태 관리
let isStreaming = false;

// 상태 업데이트 함수
function updateStatus(data) {
    // RTSP URL 동적 업데이트
    if (data.rtsp_url) {
        rtspUrlEl.textContent = data.rtsp_url;
    }
    
    // 캡처 상태 표시 (닷 인디케이터)
    if (data.is_active) {
        captureStatus.className = 'capture-status connected';
        captureText.textContent = '활성';
    } else {
        captureStatus.className = 'capture-status disconnected';
        captureText.textContent = '중지됨';
    }
    
    if (data.error_message) {
        captureStatus.className = 'capture-status disconnected';
        captureText.textContent = '에러';
    }
    
    // 버튼 상태 업데이트
    startCaptureBtn.disabled = data.is_active;
    stopCaptureBtn.disabled = !data.is_active;
    
    // 스트리밍 버튼 상태는 별도 함수로 처리
    updateStreamingButtons();
}

// Socket.IO 이벤트 핸들러
socket.on('connect', () => {
    connectionStatus.className = 'connection-status connected';
    connectionText.textContent = '연결됨';
});

socket.on('disconnect', () => {
    connectionStatus.className = 'connection-status disconnected';
    connectionText.textContent = '연결 끊김';
});

socket.on('request_client_metadata', () => {
    socket.emit('response_client_metadata', {
        client_type: "user"
    })
})

// Socket.IO 서버에서 브로드캐스트되는 이벤트들
socket.on('broadcast_caputer_status', (data) => {
    updateStatus(data);
});

socket.on('broadcast_video_frame', (data) => {
    if (data.frame_data instanceof ArrayBuffer) {
        // ImageBitmap으로 직접 처리 (Network 탭에 안보임)
        const blob = new Blob([data.frame_data], { type: 'image/jpeg' });
        
        createImageBitmap(blob).then(imageBitmap => {
            // Canvas 크기를 컨테이너에 맞게 고정 설정
            if (videoCanvas.width === 0) {
                videoCanvas.width = 800;
                videoCanvas.height = 600;
            }
            
            // 이미지 비율을 유지하면서 Canvas에 맞게 그리기
            const canvasAspect = videoCanvas.width / videoCanvas.height;
            const imageAspect = imageBitmap.width / imageBitmap.height;
            
            let drawWidth, drawHeight, drawX, drawY;
            
            if (imageAspect > canvasAspect) {
                // 이미지가 더 넓은 경우
                drawWidth = videoCanvas.width;
                drawHeight = videoCanvas.width / imageAspect;
                drawX = 0;
                drawY = (videoCanvas.height - drawHeight) / 2;
            } else {
                // 이미지가 더 높은 경우
                drawWidth = videoCanvas.height * imageAspect;
                drawHeight = videoCanvas.height;
                drawX = (videoCanvas.width - drawWidth) / 2;
                drawY = 0;
            }
            
            // Canvas 클리어 후 이미지 그리기
            ctx.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
            ctx.drawImage(imageBitmap, drawX, drawY, drawWidth, drawHeight);
            
            // Canvas 표시, 다른 요소 숨기기
            videoCanvas.style.display = 'block';
            videoFrame.style.display = 'none';
            noVideo.style.display = 'none';
            
            // 메모리 해제
            imageBitmap.close();
        }).catch(err => {
            console.error('ImageBitmap 생성 실패:', err);
        });
    }
});

// 캡처 제어 응답은 capture_status로 대체됨

socket.on('error', (data) => {
    // 에러 처리
});

// 스트리밍 응답은 capture_status로 통합됨

// 제어 함수들
function startStreaming() {
    // 스트리밍 룸 참가 요청
    socket.emit('join_streaming_room');
    isStreaming = true;
    updateStreamingButtons();
}

function startCapture() {
    socket.emit('start_capture');
    // 갭쳐 시작 후 2초 후 스트리밍 자동 시작
    setTimeout(() => {
        startStreaming();
    }, 200);
    
}
function stopStreaming() {
    // 스트리밍 룸 퇴장 요청
    socket.emit('leave_streaming_room');
    isStreaming = false;
    
    // 화면 초기화
    videoCanvas.style.display = 'none';
    videoFrame.style.display = 'none';
    noVideo.style.display = 'block';
    if (ctx) {
        ctx.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
    }
    
    updateStreamingButtons();
}

function stopCapture() {
    if (isStreaming) {
        stopStreaming(); // 비디오 캡쳐 중지 전 스트리밍 그룹에서 탈출
    }
    socket.emit('stop_capture');
    
    // 스트리밍 상태 초기화
    isStreaming = false;
    
    // 모든 비디오 요소 숨기고 기본 화면 표시
    videoFrame.style.display = 'none';
    videoCanvas.style.display = 'none';
    noVideo.style.display = 'block';
    
    // Canvas 초기화
    if (ctx) {
        ctx.clearRect(0, 0, videoCanvas.width, videoCanvas.height);
    }
}

// 스트리밍 버튼 상태 업데이트 헬퍼 함수
function updateStreamingButtons() {
    const captureActive = startCaptureBtn.disabled; // 캡처가 활성화되면 버튼이 disabled됨
    startStreamingBtn.disabled = !captureActive || isStreaming;
    stopStreamingBtn.disabled = !isStreaming;
}

// Socket.IO 연결 시 자동으로 상태를 받아옴