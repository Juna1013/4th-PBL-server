# 開発ガイド

このドキュメントでは、音声認識サーバーのカスタマイズと拡張方法を説明します。

## プロジェクト構成

```
server/
├── main.py                    # FastAPIアプリケーション
├── requirements.txt           # 依存関係
├── render.yaml               # Renderデプロイ設定
├── pico_client_example.py    # Raspberry Pi Pico Wサンプル
├── docs/                     # ドキュメント
│   ├── setup.md
│   ├── api.md
│   ├── deployment.md
│   └── development.md
└── test/                     # テストコード（今後追加予定）
```

---

## 音声認識モデルの統合

現在、`process_audio()` 関数はダミー実装になっています。実際の音声認識モデルを統合する方法を説明します。

### Option 1: OpenAI Whisper

Whisperは高精度な音声認識モデルです。

#### 1. 依存関係の追加

```bash
pip install openai-whisper
```

または `requirements.txt` に追加：
```txt
openai-whisper==20231117
```

#### 2. コードの変更

`main.py` の `process_audio()` 関数を以下のように変更：

```python
import whisper

# モデルのロード（アプリ起動時に1回だけ）
model = whisper.load_model("base")  # tiny, base, small, medium, large

def process_audio(audio_data: np.ndarray, sample_rate: int) -> tuple[str, float]:
    """音声認識処理"""
    # 音声データを一時ファイルに保存
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio_data, sample_rate)
        temp_path = f.name
    
    try:
        # Whisperで音声認識
        result = model.transcribe(temp_path, language="ja")
        recognized_text = result["text"]
        
        # コマンドにマッチング
        command = match_command(recognized_text)
        
        # 信頼度（Whisperは0〜1のスコアを返す）
        confidence = result.get("confidence", 0.9)
        
        return command, confidence
    finally:
        # 一時ファイルを削除
        import os
        os.unlink(temp_path)
```

#### 3. モデルサイズの選択

| モデル | サイズ | VRAM | 精度 |
|--------|--------|------|------|
| tiny   | 39MB   | 1GB  | 低   |
| base   | 74MB   | 1GB  | 中   |
| small  | 244MB  | 2GB  | 高   |
| medium | 769MB  | 5GB  | 非常に高 |
| large  | 1550MB | 10GB | 最高 |

Renderの無料プランでは `tiny` または `base` を推奨します。

---

### Option 2: Hugging Face Transformers

#### 1. 依存関係の追加

```bash
pip install transformers
```

#### 2. コードの実装

```python
from transformers import pipeline

# モデルのロード
recognizer = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-small",
    device=-1  # CPU使用
)

def process_audio(audio_data: np.ndarray, sample_rate: int) -> tuple[str, float]:
    """音声認識処理"""
    # リサンプリング（モデルが16kHzを期待する場合）
    if sample_rate != 16000:
        from scipy import signal
        num_samples = int(len(audio_data) * 16000 / sample_rate)
        audio_data = signal.resample(audio_data, num_samples)
    
    # 音声認識
    result = recognizer(audio_data)
    recognized_text = result["text"]
    
    # コマンドマッチング
    command = match_command(recognized_text)
    confidence = result.get("score", 0.9)
    
    return command, confidence
```

---

### Option 3: カスタムモデル

独自の音声認識モデルをトレーニングして使用する場合：

#### 1. モデルのトレーニング

Google Colabや自分のGPU環境でモデルをトレーニングします。

```python
# トレーニング例（疑似コード）
import torch
from torch import nn

class VoiceCommandModel(nn.Module):
    def __init__(self, num_commands):
        super().__init__()
        # モデルの定義
        self.conv1 = nn.Conv1d(1, 64, kernel_size=3)
        self.fc = nn.Linear(64, num_commands)
    
    def forward(self, x):
        x = self.conv1(x)
        x = torch.relu(x)
        x = torch.max_pool1d(x, x.size(2))
        x = x.view(x.size(0), -1)
        return self.fc(x)

# トレーニングループ
# ...

# モデルの保存
torch.save(model.state_dict(), "voice_model.pth")
```

#### 2. サーバーでの使用

```python
import torch

# モデルのロード
model = VoiceCommandModel(num_commands=6)
model.load_state_dict(torch.load("voice_model.pth"))
model.eval()

def process_audio(audio_data: np.ndarray, sample_rate: int) -> tuple[str, float]:
    """カスタムモデルで音声認識"""
    # 前処理
    audio_tensor = torch.tensor(audio_data).unsqueeze(0).unsqueeze(0)
    
    # 推論
    with torch.no_grad():
        output = model(audio_tensor)
        probabilities = torch.softmax(output, dim=1)
        confidence, predicted_idx = torch.max(probabilities, dim=1)
    
    # コマンドに変換
    command = SUPPORTED_COMMANDS[predicted_idx.item()]
    
    return command, confidence.item()
```

---

## コマンドのカスタマイズ

### サポートコマンドの追加

`main.py` の `SUPPORTED_COMMANDS` リストを編集：

```python
SUPPORTED_COMMANDS = [
    "前進",
    "後退",
    "左折",
    "右折",
    "停止",
    "スタート",
    "加速",        # 新規追加
    "減速",        # 新規追加
    "ライト点灯",  # 新規追加
]
```

### コマンドマッチングの改善

部分一致や類義語に対応する場合：

```python
def match_command(recognized_text: str) -> str:
    """高度なコマンドマッチング"""
    recognized_text = recognized_text.lower().strip()
    
    # コマンドと類義語のマッピング
    command_map = {
        "前進": ["前", "進む", "まえ", "ぜんしん"],
        "後退": ["後ろ", "戻る", "うしろ", "こうたい"],
        "左折": ["左", "ひだり", "させつ"],
        "右折": ["右", "みぎ", "うせつ"],
        "停止": ["止まれ", "ストップ", "とまれ", "ていし"],
        "スタート": ["開始", "始め", "かいし", "スタート"],
    }
    
    # マッチング
    for command, synonyms in command_map.items():
        for synonym in synonyms:
            if synonym in recognized_text:
                return command
    
    # マッチしない場合はデフォルト
    return "停止"
```

---

## ロギングとデバッグ

### ログレベルの設定

```python
import logging

# 開発環境
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 本番環境
logging.basicConfig(level=logging.INFO)
```

### デバッグ情報の追加

```python
@app.post("/recognize")
async def recognize_audio(audio: UploadFile = File(...)):
    logger.debug(f"受信ファイル名: {audio.filename}")
    logger.debug(f"Content-Type: {audio.content_type}")
    
    contents = await audio.read()
    logger.debug(f"ファイルサイズ: {len(contents)} bytes")
    
    # ... 処理 ...
```

---

## テストの追加

### 単体テスト

`test/test_main.py` を作成：

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """ヘルスチェックのテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_commands():
    """コマンド一覧のテスト"""
    response = client.get("/commands")
    assert response.status_code == 200
    assert "commands" in response.json()
    assert len(response.json()["commands"]) > 0
```

### テストの実行

```bash
pip install pytest
pytest test/
```

---

## パフォーマンス最適化

### 1. モデルのキャッシュ

モデルを起動時に1回だけロードし、リクエストごとに再利用：

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def load_model():
    """モデルをキャッシュ"""
    return whisper.load_model("base")

model = load_model()
```

### 2. 非同期処理

重い処理を非同期化：

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor()

@app.post("/recognize")
async def recognize_audio(audio: UploadFile = File(...)):
    contents = await audio.read()
    audio_data, sample_rate = sf.read(io.BytesIO(contents))
    
    # CPUバウンドな処理を別プロセスで実行
    loop = asyncio.get_event_loop()
    command, confidence = await loop.run_in_executor(
        executor,
        process_audio,
        audio_data,
        sample_rate
    )
    
    return CommandResponse(
        success=True,
        command=command,
        confidence=confidence
    )
```

---

## Raspberry Pi Pico W との統合

### マイク録音の実装

Pico側でマイクから音声を録音する例：

```python
# Raspberry Pi Pico W
from machine import Pin, ADC, Timer
import array

# マイク設定（ADC）
mic = ADC(Pin(26))  # GP26にマイクを接続

# サンプリング設定
SAMPLE_RATE = 16000
DURATION = 2  # 秒
samples = array.array('H', [0] * (SAMPLE_RATE * DURATION))

def record_audio():
    """音声録音"""
    for i in range(len(samples)):
        samples[i] = mic.read_u16()
    return samples

# 録音して送信
audio_data = record_audio()
send_audio(audio_data)
```

---

## トラブルシューティング

### メモリ不足

大きなモデルを使用する場合、メモリ不足になることがあります：

**解決策:**
1. より小さなモデルを使用（tiny, base）
2. 有料プランにアップグレード
3. 音声ファイルのサイズを制限

### 推論が遅い

**解決策:**
1. CPU最適化版のPyTorchを使用
2. 量子化モデルを使用
3. より小さなモデルを選択
