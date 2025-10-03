from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from ..models.speech_recognition import get_speech_model
from ..models.data_store import data_store

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech", tags=["speech"])

class SpeechPredictionResponse(BaseModel):
    """音声予測レスポンスモデル"""
    success: bool
    predicted_command: Optional[str] = None
    confidence: Optional[float] = None
    is_confident: Optional[bool] = None
    all_predictions: Optional[List[dict]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

class ModelInfoResponse(BaseModel):
    """モデル情報レスポンスモデル"""
    success: bool
    model_info: Optional[dict] = None
    error: Optional[str] = None
    timestamp: str

def create_error_response(message: str, details: Optional[str] = None) -> dict:
    """エラーレスポンスを作成"""
    return {
        "success": False,
        "error": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }

def create_success_response(data: dict, message: Optional[str] = None) -> dict:
    """成功レスポンスを作成"""
    response = {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        **data
    }
    if message:
        response["message"] = message
    return response

@router.post("/predict", response_model=SpeechPredictionResponse)
async def predict_speech_command(
    audio_file: UploadFile = File(...),
    confidence_threshold: float = 0.7,
    auto_execute: bool = False
):
    """
    音声ファイルからコマンドを予測
    
    Args:
        audio_file: 音声ファイル（WAV, MP3など）
        confidence_threshold: 信頼度の閾値（デフォルト: 0.7）
        auto_execute: 予測結果を自動実行するか（デフォルト: False）
    
    Returns:
        SpeechPredictionResponse: 予測結果
    """
    try:
        # モデルが初期化されているか確認
        model = get_speech_model()
        if model is None:
            return create_error_response(
                "音声認識モデルが初期化されていません",
                "サーバー管理者にお問い合わせください"
            )
        
        # ファイル形式の確認
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            return create_error_response(
                "無効なファイル形式です",
                "音声ファイル（WAV、MP3など）をアップロードしてください"
            )
        
        # ファイルサイズの確認（10MB制限）
        max_file_size = 10 * 1024 * 1024  # 10MB
        audio_data = await audio_file.read()
        if len(audio_data) > max_file_size:
            return create_error_response(
                "ファイルサイズが大きすぎます",
                f"ファイルサイズは{max_file_size // (1024*1024)}MB以下にしてください"
            )
        
        # 音声認識実行
        try:
            predicted_command, confidence, all_predictions = model.predict(audio_data)
            is_confident = model.is_confident_prediction(confidence, confidence_threshold)
            
            # 予測結果をフォーマット
            formatted_predictions = [
                {
                    "command": cmd,
                    "confidence": conf,
                    "percentage": f"{conf * 100:.1f}%"
                }
                for cmd, conf in all_predictions
            ]
            
            # 自動実行が有効で、信頼度が十分な場合はコマンドを実行
            executed = False
            if auto_execute and is_confident:
                # コマンドを有効なコマンドリストと照合
                valid_commands = ["GO", "RIGHT", "LEFT", "STOP"]
                command_upper = predicted_command.upper()
                
                # "go" -> "FORWARD" の変換
                if command_upper == "GO":
                    command_upper = "FORWARD"
                
                if command_upper in valid_commands:
                    try:
                        data_store.add_log(command_upper)
                        executed = True
                        logger.info(f"音声コマンドを自動実行: {command_upper}")
                    except Exception as e:
                        logger.error(f"コマンド自動実行に失敗: {str(e)}")
            
            # レスポンス作成
            response_data = {
                "predicted_command": predicted_command,
                "confidence": round(confidence, 4),
                "confidence_percentage": f"{confidence * 100:.1f}%",
                "is_confident": is_confident,
                "threshold_used": confidence_threshold,
                "all_predictions": formatted_predictions,
                "auto_executed": executed
            }
            
            message = f"音声認識完了: {predicted_command} (信頼度: {confidence * 100:.1f}%)"
            if executed:
                message += " - コマンドを自動実行しました"
            elif auto_execute and not is_confident:
                message += " - 信頼度が低いため自動実行されませんでした"
            
            return create_success_response(response_data, message)
            
        except Exception as e:
            logger.error(f"音声認識処理でエラー: {str(e)}")
            return create_error_response(
                "音声認識処理に失敗しました",
                str(e)
            )
            
    except Exception as e:
        logger.error(f"音声認識APIでエラー: {str(e)}")
        return create_error_response(
            "サーバーエラーが発生しました",
            str(e)
        )

@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    音声認識モデルの情報を取得
    
    Returns:
        ModelInfoResponse: モデル情報
    """
    try:
        model = get_speech_model()
        if model is None:
            return create_error_response(
                "音声認識モデルが初期化されていません"
            )
        
        model_info = model.get_model_info()
        
        return create_success_response({
            "model_info": model_info
        }, "モデル情報を取得しました")
        
    except Exception as e:
        logger.error(f"モデル情報取得でエラー: {str(e)}")
        return create_error_response(
            "モデル情報の取得に失敗しました",
            str(e)
        )

@router.get("/commands")
async def get_supported_commands():
    """
    サポートされている音声コマンド一覧を取得
    
    Returns:
        dict: サポートコマンド情報
    """
    try:
        model = get_speech_model()
        if model is None:
            return create_error_response(
                "音声認識モデルが初期化されていません"
            )
        
        commands_info = {
            "supported_commands": model.commands,
            "command_mapping": {
                "go": "FORWARD - 前進",
                "right": "RIGHT - 右折", 
                "left": "LEFT - 左折",
                "stop": "STOP - 停止"
            },
            "usage_notes": [
                "音声は明瞭に発話してください",
                "約1秒程度の音声が最適です",
                "背景ノイズが少ない環境で録音してください"
            ]
        }
        
        return create_success_response({
            "commands_info": commands_info
        }, "サポートコマンド一覧を取得しました")
        
    except Exception as e:
        logger.error(f"コマンド一覧取得でエラー: {str(e)}")
        return create_error_response(
            "コマンド一覧の取得に失敗しました",
            str(e)
        )

@router.post("/test")
async def test_speech_recognition():
    """
    音声認識機能のテスト（開発用）
    
    Returns:
        dict: テスト結果
    """
    try:
        model = get_speech_model()
        if model is None:
            return create_error_response(
                "音声認識モデルが初期化されていません"
            )
        
        # モデルの基本情報を取得
        model_info = model.get_model_info()
        
        test_result = {
            "model_status": "OK",
            "model_loaded": True,
            "supported_commands": model.commands,
            "model_info": model_info,
            "api_endpoints": [
                "/api/speech/predict - 音声認識予測",
                "/api/speech/model/info - モデル情報取得", 
                "/api/speech/commands - サポートコマンド一覧"
            ]
        }
        
        return create_success_response({
            "test_result": test_result
        }, "音声認識テストが正常に完了しました")
        
    except Exception as e:
        logger.error(f"音声認識テストでエラー: {str(e)}")
        return create_error_response(
            "音声認識テストに失敗しました",
            str(e)
        )