from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
import threading
from collections import Counter

class LogEntry(BaseModel):
    id: int
    word: str
    timestamp: datetime

class CommandResponse(BaseModel):
    command: Optional[str]
    timestamp: datetime

class LogResponse(BaseModel):
    success: bool
    message: str
    data: LogEntry

class StatsResponse(BaseModel):
    total_commands: int
    last_command: Optional[str]
    command_counts: Dict[str, int]
    last_update: Optional[datetime]

class DataStore:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DataStore, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._command: Optional[str] = None
        self._logs: List[LogEntry] = []
        self._id_counter: int = 1
        self._initialized = True
    
    def get_command(self) -> Optional[str]:
        """最新コマンドを取得"""
        return self._command
    
    def add_log(self, word: str) -> LogEntry:
        """新しいログを追加し、コマンドを更新"""
        with self._lock:
            log_entry = LogEntry(
                id=self._id_counter,
                word=word.upper(),
                timestamp=datetime.now()
            )
            
            self._logs.append(log_entry)
            self._command = word.upper()
            self._id_counter += 1
            
            # 最新50件のみ保持（メモリ節約）
            if len(self._logs) > 50:
                self._logs = self._logs[-50:]
            
            return log_entry
    
    def get_logs(self, limit: int = 20) -> List[LogEntry]:
        """ログ一覧を取得（新しい順）"""
        return list(reversed(self._logs))[:limit]
    
    def get_stats(self) -> dict:
        """統計情報を取得"""
        if not self._logs:
            return {
                "total_commands": 0,
                "last_command": None,
                "command_counts": {},
                "last_update": None
            }
        
        command_counts = Counter(log.word for log in self._logs)
        
        return {
            "total_commands": len(self._logs),
            "last_command": self._command,
            "command_counts": dict(command_counts),
            "last_update": self._logs[-1].timestamp if self._logs else None
        }

# シングルトンインスタンス
data_store = DataStore()
