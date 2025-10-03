from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from dotenv import load_dotenv
import logging

from .api.routes import router
from .api.speech_routes import router as speech_router
from .models.speech_recognition import initialize_speech_model

# 環境変数読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Line Tracer Control API",
    description="ライントレースカー制御システムのバックエンドAPI（音声認識機能付き）",
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
app.include_router(speech_router, prefix="/api")

# 音声認識モデルの初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    try:
        # 音声認識モデルのパスを設定（サーバーディレクトリ内のモデルを使用）
        model_path = os.path.join(os.path.dirname(__file__), "..", "models", "speech_cnn.h5")
        model_path = os.path.abspath(model_path)
        
        if os.path.exists(model_path):
            initialize_speech_model(model_path)
            logger.info(f"音声認識モデルが正常に初期化されました: {model_path}")
        else:
            logger.warning(f"音声認識モデルが見つかりません: {model_path}")
            logger.warning("音声認識機能は無効になります")
    except Exception as e:
        logger.error(f"音声認識モデルの初期化に失敗しました: {str(e)}")
        logger.warning("音声認識機能は無効になります")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Line Tracer Control API",
        "description": "ライントレースカー制御システムのバックエンドAPI（音声認識機能付き）",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "command": "/api/command",
            "logs": "/api/logs",
            "stats": "/api/stats",
            "speech_predict": "/api/speech/predict",
            "speech_model_info": "/api/speech/model/info",
            "speech_commands": "/api/speech/commands",
            "documentation": "/docs"
        },
        "features": [
            "ライントレースカー制御",
            "音声コマンド認識",
            "リアルタイム通信",
            "ログ管理"
        ]
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
