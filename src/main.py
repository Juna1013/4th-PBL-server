from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import io
import soundfile as sf
from typing import Optional
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Raspberry Pi Pico W 音声認識サーバー",
    description="Raspberry Pi Pico Wからの音声信号を受信し、コマンドを判別するAPI",
    version="1.0.0"
)

# CORS設定（開発時のため全許可、本番環境では制限すること）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# レスポンスモデル
class CommandResponse(BaseModel):
    success: bool
    command: str
    confidence: float
    message: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    message: str

# サポートするコマンド一覧
SUPPORTED_COMMANDS = [
    "前進",
    "後退",
    "左折",
    "右折",
    "停止",
    "スタート",
]

@app.get("/", response_model=HealthResponse)
async def root():
    """
    APIサーバーのヘルスチェック
    """
    return HealthResponse(
        status="ok",
        message="音声認識サーバーは正常に動作しています"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    ヘルスチェックエンドポイント（Render用）
    """
    return HealthResponse(
        status="healthy",
        message="Server is running"
    )

@app.get("/commands")
async def get_commands():
    """
    サポートされているコマンド一覧を取得
    """
    return {
        "commands": SUPPORTED_COMMANDS,
        "count": len(SUPPORTED_COMMANDS)
    }

@app.post("/recognize", response_model=CommandResponse)
async def recognize_audio(audio: UploadFile = File(...)):
    """
    Raspberry Pi Pico Wから送信された音声データを解析してコマンドを返却
    
    Args:
        audio: 音声ファイル（WAV形式推奨）
        
    Returns:
        CommandResponse: 認識されたコマンドと信頼度
    """
    try:
        # 音声ファイルの読み込み
        contents = await audio.read()
        
        # 音声データをnumpy配列に変換
        audio_data, sample_rate = sf.read(io.BytesIO(contents))
        
        logger.info(f"音声データ受信: サンプルレート={sample_rate}Hz, 長さ={len(audio_data)}サンプル")
        
        # ここで実際の音声認識モデルを使用する
        # 現在はダミーの実装
        recognized_command, confidence = process_audio(audio_data, sample_rate)
        
        return CommandResponse(
            success=True,
            command=recognized_command,
            confidence=confidence,
            message=f"コマンド '{recognized_command}' を認識しました"
        )
        
    except Exception as e:
        logger.error(f"音声認識エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"音声認識処理に失敗しました: {str(e)}"
        )

def process_audio(audio_data: np.ndarray, sample_rate: int) -> tuple[str, float]:
    """
    音声データを処理してコマンドを認識する
    
    この関数は現在ダミー実装です。
    実際の音声認識モデル（例: Whisper, Wav2Vec2など）をここに統合してください。
    
    Args:
        audio_data: 音声データ（numpy配列）
        sample_rate: サンプリングレート
        
    Returns:
        tuple[str, float]: (認識されたコマンド, 信頼度)
    """
    # TODO: 実際の音声認識モデルの実装
    # 現在はランダムにコマンドを返すダミー実装
    
    # 音声の特徴量を抽出（例：エネルギー）
    energy = np.sum(audio_data ** 2)
    
    # ダミー: エネルギーに基づいて簡単な判定
    if energy < 0.01:
        return "停止", 0.85
    elif energy < 0.1:
        return "前進", 0.90
    else:
        return "スタート", 0.88
    
    # 実際の実装では以下のようなモデルを使用:
    # from transformers import pipeline
    # recognizer = pipeline("automatic-speech-recognition", model="openai/whisper-small")
    # result = recognizer(audio_data)
    # return match_command(result["text"]), result["score"]

def match_command(recognized_text: str) -> str:
    """
    認識されたテキストからサポートされているコマンドにマッチング
    
    Args:
        recognized_text: 音声認識結果のテキスト
        
    Returns:
        str: マッチしたコマンド
    """
    recognized_text = recognized_text.strip()
    
    for command in SUPPORTED_COMMANDS:
        if command in recognized_text:
            return command
    
    # マッチしない場合はデフォルト
    return "停止"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
