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

class CommandRequest(BaseModel):
    word: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

@router.get("/command", response_model=CommandResponse)
async def get_command():
    """最新コマンドを取得"""
    try:
        command = data_store.get_command()
        return CommandResponse(
            command=command,
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
            raise HTTPException(
                status_code=400, 
                detail="word is required and must not be empty"
            )
        
        word_upper = word.upper()
        if word_upper not in VALID_COMMANDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid command. Valid commands: {', '.join(VALID_COMMANDS)}"
            )
        
        log_entry = data_store.add_log(word_upper)
        
        return {
            "success": True,
            "message": "Command logged successfully",
            "data": {
                "id": log_entry.id,
                "word": log_entry.word,
                "timestamp": log_entry.timestamp.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_logs(limit: int = 20):
    """ログ一覧を取得"""
    try:
        if limit <= 0 or limit > 100:
            limit = 20
            
        logs = data_store.get_logs(limit)
        
        return {
            "success": True,
            "data": [
                {
                    "id": log.id,
                    "word": log.word,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ],
            "total": len(logs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "Line Tracer Control API"
    }
