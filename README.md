# 音声認識サーバー

Raspberry Pi Pico Wからの音声信号を受信し、音声認識を行ってコマンドを返すFastAPIサーバーです。

## 🎯 プロジェクト概要

このプロジェクトは、Raspberry Pi Pico Wで録音した音声をWiFi経由でサーバーに送信し、音声認識によってロボット制御コマンドを取得するシステムです。

### 主な機能

- 🎤 音声ファイルのアップロードと認識
- 🤖 ロボット制御コマンドの返却（前進、後退、左折、右折、停止、スタート）
- 📡 Raspberry Pi Pico W との WiFi通信対応
- ☁️ Renderへの簡単デプロイ

### 技術スタック

- **バックエンド**: FastAPI
- **音声処理**: librosa, soundfile, NumPy
- **AI/ML**: PyTorch（将来的な音声認識モデル用）
- **デプロイ**: Render

## 🚀 クイックスタート

### 必要な環境

- Python 3.10 以上
- pip

### インストールと起動

```bash
# 依存関係のインストール
pip install -r requirements.txt

# サーバーの起動
python main.py
```

サーバーが起動したら、以下のURLにアクセス：
- **API**: http://localhost:8000
- **ドキュメント**: http://localhost:8000/docs

## 📚 ドキュメント

詳細なドキュメントは `docs/` ディレクトリにあります：

- **[セットアップガイド](docs/setup.md)** - ローカル開発環境の構築方法
- **[API仕様](docs/api.md)** - エンドポイントとデータモデルの詳細
- **[デプロイガイド](docs/deployment.md)** - Renderへのデプロイ手順
- **[開発ガイド](docs/development.md)** - 音声認識モデルの統合とカスタマイズ方法
- **[Pico W 統合ガイド](docs/pico_integration.md)** - Raspberry Pi Pico W との連携方法

## 🎯 サポートコマンド

現在、以下のコマンドに対応しています：

- 前進
- 後退
- 左折
- 右折
- 停止
- スタート

## 📡 使用例

### curlでのテスト

```bash
curl -X POST "http://localhost:8000/recognize" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@test_audio.wav"
```

### Raspberry Pi Pico W から

詳細は [Pico W 統合ガイド](docs/pico_integration.md) を参照してください。

```python
import urequests
import network

# WiFi接続
wlan = network.WLAN(network.STA_IF)
wlan.connect("SSID", "PASSWORD")

# 音声送信
url = "https://your-app.onrender.com/recognize"
files = {"audio": ("audio.wav", audio_data, "audio/wav")}
response = urequests.post(url, files=files)
print(response.json()["command"])
```

## 🛠️ 現在の実装状態

⚠️ **注意**: 現在は **ダミー実装** です。音声データを受け取ってサンプルのコマンドを返しますが、実際の音声認識は行っていません。

実際の音声認識モデルを統合する方法は [開発ガイド](docs/development.md) を参照してください。

## 🌐 デプロイ

Renderへのデプロイは非常に簡単です：

1. GitHubにプッシュ
2. Renderでリポジトリを接続
3. 自動デプロイ完了

詳細は [デプロイガイド](docs/deployment.md) を参照してください。

## 📁 プロジェクト構成

```
server/
├── main.py                    # エントリーポイント（src/main.py のラッパー）
├── requirements.txt           # Python依存関係
├── render.yaml               # Render設定
├── src/                      # ソースコード
│   ├── __init__.py
│   ├── main.py               # FastAPIアプリケーション
│   ├── speech_recognizer.py  # 音声認識モジュール
│   ├── pico_client_example.py # Pico Wサンプルコード
│   └── models/               # 機械学習モデル
│       └── __init__.py
├── colab/                    # Colabトレーニング用
│   ├── model/                # 学習済みモデル
│   │   ├── speech_cnn.h5
│   │   ├── speech_cnn.tflite
│   │   └── train_cnn_model.py
│   └── requirements.txt
├── test/                     # テスト
│   └── server.py
└── docs/                     # ドキュメント
    ├── setup.md
    ├── api.md
    ├── deployment.md
    ├── development.md
    └── pico_integration.md
```

## 🤝 貢献

このプロジェクトはPBL（Project Based Learning）の教材として開発されています。

## 📄 ライセンス

MIT License

## 🔗 関連リンク

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Render](https://render.com)
- [Raspberry Pi Pico W](https://www.raspberrypi.com/products/raspberry-pi-pico/)
