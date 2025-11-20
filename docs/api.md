# API仕様

このドキュメントでは、音声認識サーバーが提供するAPIエンドポイントの詳細を説明します。

## ベースURL

- ローカル開発: `http://localhost:8000`
- 本番環境: `https://your-app.onrender.com`

## エンドポイント一覧

### 1. ヘルスチェック

サーバーの稼働状態を確認します。

**エンドポイント:**
```
GET /
GET /health
```

**レスポンス:**
```json
{
  "status": "healthy",
  "message": "Server is running"
}
```

**ステータスコード:**
- `200 OK` - サーバーは正常に動作しています

---

### 2. サポートコマンド一覧

サーバーが認識できるコマンドの一覧を取得します。

**エンドポイント:**
```
GET /commands
```

**レスポンス:**
```json
{
  "commands": [
    "前進",
    "後退",
    "左折",
    "右折",
    "停止",
    "スタート"
  ],
  "count": 6
}
```

**ステータスコード:**
- `200 OK` - コマンド一覧を正常に取得

---

### 3. 音声認識

音声ファイルをアップロードして、コマンドを認識します。

**エンドポイント:**
```
POST /recognize
```

**リクエスト:**

- **Content-Type:** `multipart/form-data`
- **パラメータ:**
  - `audio` (required): 音声ファイル（WAV形式推奨）

**リクエスト例（curl）:**
```bash
curl -X POST "http://localhost:8000/recognize" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@audio.wav"
```

**レスポンス（成功）:**
```json
{
  "success": true,
  "command": "前進",
  "confidence": 0.92,
  "message": "コマンド '前進' を認識しました"
}
```

**レスポンス（失敗）:**
```json
{
  "detail": "音声認識処理に失敗しました: エラーメッセージ"
}
```

**ステータスコード:**
- `200 OK` - 音声認識成功
- `500 Internal Server Error` - 音声認識処理に失敗

---

## データモデル

### CommandResponse

音声認識結果のレスポンスモデル

| フィールド | 型 | 説明 |
|----------|-----|------|
| success | boolean | 認識が成功したかどうか |
| command | string | 認識されたコマンド |
| confidence | float | 認識の信頼度（0.0〜1.0） |
| message | string (optional) | 補足メッセージ |

### HealthResponse

ヘルスチェックのレスポンスモデル

| フィールド | 型 | 説明 |
|----------|-----|------|
| status | string | ステータス（"healthy", "ok"など） |
| message | string | ステータスメッセージ |

---

## Swagger UI

サーバーを起動後、以下のURLでインタラクティブなAPIドキュメントにアクセスできます：

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Swagger UIでは、ブラウザから直接APIをテストできます。

---

## 音声ファイルの要件

### 推奨フォーマット
- **形式:** WAV (PCM)
- **サンプリングレート:** 16000 Hz
- **ビット深度:** 16 bit
- **チャンネル:** モノラル
- **ファイルサイズ:** 10MB以下

### その他のサポート形式
- MP3
- FLAC
- OGG

ただし、WAV形式が最も安定しています。

---

## エラーハンドリング

### エラーレスポンス形式

```json
{
  "detail": "エラーメッセージ"
}
```

### よくあるエラー

| エラーメッセージ | 原因 | 解決方法 |
|---------------|------|---------|
| "音声認識処理に失敗しました" | 音声ファイルの形式が不正 | WAV形式に変換してください |
| "File too large" | ファイルサイズが大きすぎる | 10MB以下に圧縮してください |
| "Invalid audio format" | サポートされていない形式 | WAV/MP3/FLACを使用してください |

---

## レート制限

現在、レート制限は設定されていません。本番環境では適切なレート制限の追加を検討してください。

---

## CORS設定

開発時は全てのオリジンからのアクセスを許可していますが、本番環境では `main.py` の CORS設定を制限してください：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```
