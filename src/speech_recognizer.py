"""
音声認識モデルのロードと推論を行うモジュール
"""

import tensorflow as tf
import numpy as np
import io
import soundfile as sf
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# モデルファイルのパス（src/から../colab/model にアクセス）
MODEL_PATH = Path(__file__).parent.parent / "colab" / "model" / "speech_cnn.h5"

# コマンドのマッピング
COMMAND_MAPPING = {
    0: "前進",    # go
    1: "右折",    # right
    2: "左折",    # left
    3: "停止",    # stop
}

class SpeechRecognizer:
    """音声認識クラス"""
    
    def __init__(self, model_path: str = None):
        """
        初期化
        
        Args:
            model_path: モデルファイルのパス（指定しない場合はデフォルト）
        """
        if model_path is None:
            model_path = MODEL_PATH
        
        logger.info(f"モデルをロード中: {model_path}")
        
        try:
            self.model = tf.keras.models.load_model(str(model_path))
            logger.info("モデルのロード成功")
        except Exception as e:
            logger.error(f"モデルのロードに失敗: {e}")
            raise
    
    def preprocess_audio(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        音声データを前処理してスペクトログラムに変換
        
        Args:
            audio_data: 音声データ（numpy配列）
            sample_rate: サンプリングレート
            
        Returns:
            np.ndarray: 前処理済みスペクトログラム
        """
        # モノラルに変換（ステレオの場合）
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # 16kHzにリサンプリング（必要な場合）
        if sample_rate != 16000:
            import scipy.signal as signal
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = signal.resample(audio_data, num_samples)
        
        # 正規化
        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # TensorFlowテンソルに変換
        audio_tensor = tf.constant(audio_data, dtype=tf.float32)
        
        # STFT（短時間フーリエ変換）でスペクトログラム作成
        spectrogram = tf.signal.stft(
            audio_tensor,
            frame_length=128,
            frame_step=64
        )
        spectrogram = tf.abs(spectrogram)
        spectrogram = tf.expand_dims(spectrogram, -1)
        
        # 時間軸を128フレームに固定
        spectrogram = tf.image.resize(spectrogram, [128, spectrogram.shape[1]])
        
        # バッチ次元を追加
        spectrogram = tf.expand_dims(spectrogram, 0)
        
        return spectrogram.numpy()
    
    def recognize(self, audio_data: np.ndarray, sample_rate: int) -> tuple[str, float]:
        """
        音声データからコマンドを認識
        
        Args:
            audio_data: 音声データ
            sample_rate: サンプリングレート
            
        Returns:
            tuple[str, float]: (認識されたコマンド, 信頼度)
        """
        try:
            # 前処理
            spectrogram = self.preprocess_audio(audio_data, sample_rate)
            
            # 推論
            predictions = self.model.predict(spectrogram, verbose=0)
            
            # 最も確率が高いクラスを取得
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            # コマンドにマッピング
            command = COMMAND_MAPPING.get(predicted_class, "停止")
            
            logger.info(f"認識結果: {command} (信頼度: {confidence:.2f})")
            
            return command, confidence
            
        except Exception as e:
            logger.error(f"音声認識エラー: {e}")
            # エラー時はデフォルトで停止
            return "停止", 0.0

# グローバルインスタンス（起動時に1回だけロード）
_recognizer = None

def get_recognizer() -> SpeechRecognizer:
    """
    音声認識インスタンスを取得（シングルトンパターン）
    """
    global _recognizer
    if _recognizer is None:
        _recognizer = SpeechRecognizer()
    return _recognizer
