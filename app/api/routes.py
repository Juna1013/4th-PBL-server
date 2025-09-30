from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..models.data_store import (
    data_store, 
    LogEntry, 
    CommandResponse, 
    LogResponse, 
    StatsResponse
)

router = APIRouter()

# バリデーション用の有効コマンド
VALID_COMMANDS = ["LEFT", "RIGHT", "FORWARD", "STOP", "BACK"]

# エラーレスポンス用のヘルパー関数
def create_error_response(message: str, code: int = 400, details: Optional[str] = None):
    """統一されたエラーレスポンスを作成"""
    error_data = {
        "success": False,
        "error": message,
        "error_code": code,
        "timestamp": datetime.now().isoformat()
    }
    if details:
        error_data["details"] = details
    return error_data

def create_success_response(data: Optional[dict] = None, message: Optional[str] = None):
    """統一された成功レスポンスを作成"""
    response = {
        "success": True,
        "timestamp": datetime.now().isoformat()
    }
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response

class CommandRequest(BaseModel):
    word: str

class PicoStatusRequest(BaseModel):
    status: str
    timestamp: Optional[float] = None

class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

@router.get("/command", response_model=CommandResponse)
async def get_command():
    """最新コマンドを取得"""
    try:
        command = data_store.get_command()
        # デフォルト値として「待機中」を設定
        display_command = command if command else "待機中"

        return CommandResponse(
            command=display_command,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log")
async def add_log(request: CommandRequest):
    """新しいコマンドログを追加"""
    try:
        word = request.word.strip()

        if not word:
            return create_error_response(
                "コマンドが空です。有効なコマンドを入力してください。",
                400,
                f"有効なコマンド: {', '.join(VALID_COMMANDS)}"
            )

        word_upper = word.upper()
        if word_upper not in VALID_COMMANDS:
            return create_error_response(
                f"無効なコマンド: {word}",
                400,
                f"有効なコマンド: {', '.join(VALID_COMMANDS)}"
            )

        log_entry = data_store.add_log(word_upper)

        return create_success_response(
            data={
                "id": log_entry.id,
                "word": log_entry.word,
                "timestamp": log_entry.timestamp.isoformat(),
                "command_display": f"{log_entry.word} コマンドを実行"
            },
            message="コマンドが正常に登録されました"
        )

    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            "サーバーエラーが発生しました",
            500,
            str(e)
        )

@router.get("/logs")
async def get_logs(limit: int = 20):
    """ログ一覧を取得"""
    try:
        if limit <= 0 or limit > 100:
            limit = 20

        logs = data_store.get_logs(limit)

        return create_success_response(
            data=[
                {
                    "id": log.id,
                    "word": log.word,
                    "timestamp": log.timestamp.isoformat(),
                    "display_time": log.timestamp.strftime("%H:%M:%S"),
                    "display_date": log.timestamp.strftime("%m/%d"),
                    "command_display": f"{log.word} コマンド"
                }
                for log in logs
            ],
            message=f"{len(logs)}件のログを取得しました"
        )

    except Exception as e:
        return create_error_response(
            "ログの取得に失敗しました",
            500,
            str(e)
        )

@router.get("/stats")
async def get_stats():
    """統計情報を取得"""
    try:
        stats = data_store.get_stats()
        
        # datetimeをISO文字列に変換
        if stats["last_update"]:
            stats["last_update"] = stats["last_update"].isoformat()
            
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/command/latest")
async def get_latest_command():
    """Pico W用の最新コマンド取得エンドポイント"""
    try:
        command = data_store.get_command()
        # デフォルト値として「STOP」を設定
        display_command = command if command else "STOP"

        return create_success_response(
            data={
                "command": display_command,
                "timestamp": datetime.now().isoformat()
            },
            message="最新コマンドを取得しました"
        )
    except Exception as e:
        return create_error_response(
            "コマンドの取得に失敗しました",
            500,
            str(e)
        )

@router.post("/pico/status")
async def update_pico_status(request: PicoStatusRequest):
    """Pico Wからのステータス更新"""
    try:
        status = request.status.strip()
        timestamp = request.timestamp if request.timestamp else datetime.now().timestamp()

        # ステータスをログとして記録（将来の拡張用）
        print(f"Pico W ステータス: {status} at {datetime.fromtimestamp(timestamp)}")

        return create_success_response(
            data={
                "received_status": status,
                "server_timestamp": datetime.now().isoformat()
            },
            message="ステータスを受信しました"
        )
    except Exception as e:
        return create_error_response(
            "ステータス更新に失敗しました",
            500,
            str(e)
        )

@router.get("/health")
async def health_check():
    """ヘルスチェック"""
    stats = data_store.get_stats()

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "Line Tracer Control API",
        "version": "1.0.0",
        "uptime": "active",
        "stats": {
            "total_commands": stats["total_commands"],
            "last_command": stats["last_command"],
            "is_active": stats["total_commands"] > 0
        }
    }
