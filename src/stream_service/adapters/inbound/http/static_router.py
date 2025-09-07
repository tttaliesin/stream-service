from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 정적 파일 경로
STATIC_DIR = Path(__file__).parent.parent.parent.parent / "static"

router = APIRouter()

# 정적 파일 마운트 (CSS, JS, 이미지 등)
router.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@router.get("/")
async def serve_index():
    """메인 페이지 제공"""
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/index.html")
async def serve_index_html():
    """인덱스 페이지 제공"""
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/style.css")
async def serve_css():
    """CSS 파일 제공"""
    return FileResponse(STATIC_DIR / "style.css")


@router.get("/app.js")
async def serve_js():
    """JavaScript 파일 제공"""
    return FileResponse(STATIC_DIR / "app.js")