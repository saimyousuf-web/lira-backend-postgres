from fastapi.middleware.cors import CORSMiddleware

def cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "*",
            "https://dpc1kyz2qo8jh.cloudfront.net",
            "http://localhost:3000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Chat-Id"],
    )
    return app
