from fastapi import FastAPI

from stream_service.infrastructure.config.container import Container


def create_app() -> FastAPI:
    container = Container()
    container.wire(modules=["stream_service.infrastructure.adapters.input.stream_router"])
    
    app = FastAPI(title="Stream Service", version="0.1.0")
    app.container = container
    
    from stream_service.infrastructure.adapters.input.stream_router import router
    app.include_router(router)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
