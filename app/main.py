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
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# 本番環境でのフロントエンドURL追加
if frontend_url := os.getenv("FRONTEND_URL"):
    allowed_origins.append(frontend_url)

# 開発環境では追加のローカルアドレスも許可
if os.getenv("ENVIRONMENT") != "production":
    allowed_origins.extend([
        "http://192.168.3.152:5173",  # ネットワーク内アドレス
        "http://10.0.0.0/8",          # プライベートネットワーク
        "http://172.16.0.0/12",
        "http://192.168.0.0/16",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    max_age=3600,  # プリフライトリクエストのキャッシュ時間
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
        "description": "ライントレースカー制御システムのバックエンドAPI",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "command": "/api/command",
            "logs": "/api/logs",
            "stats": "/api/stats",
            "documentation": "/docs"
        }
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
