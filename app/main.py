from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from dotenv import load_dotenv

from .api.routes import router

# 環境変数読み込み
load_dotenv()

app = FastAPI(
    title="Line Tracer Control API",
    description="ライントレースカー制御システムのバックエンドAPI",
    version="1.0.0"
)

# CORS設定
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# 本番環境でのフロントエンドURL追加
if frontend_url := os.getenv("FRONTEND_URL"):
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host ミドルウェア（本番環境用）
if os.getenv("ENVIRONMENT") == "production":
    allowed_hosts = ["*"]  # 本番では適切なホスト名を設定
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# ルート登録
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Line Tracer Control API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") != "production"
    )
