# テストサーバー

`test/server.py` はシンプルなテスト用 FastAPI サーバーです。

## 概要

このテストサーバーは、基本的な HTTP エンドポイントのテストと、通信確認に使用されます。

## エンドポイント

### GET /ping

サーバーが正常に動作しているかを確認するヘルスチェックエンドポイントです。

**リクエスト:**
```bash
curl -X GET http://localhost:8000/ping
```

**レスポンス:**
```json
{
  "message": "pong"
}
```

**ステータスコード:** `200 OK`

## 実行方法

### 直接実行

```bash
cd server
python test/server.py
```

サーバーが起動すると、以下が表示されます：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### uvicorn を使用

```bash
uvicorn test.server:app --host 0.0.0.0 --port 8000
```

## テスト方法

### curl でのテスト

```bash
curl -X GET http://localhost:8000/ping
```

### Python での実行

```python
import requests

response = requests.get("http://localhost:8000/ping")
print(response.json())
print(response.status_code)
```

### 結果

```python
{'message': 'pong'}
200
```

## 用途

- **接続確認**: サーバーが起動しているか確認
- **ネットワークテスト**: 別のマシンからの疎通確認
- **CI/CD パイプライン**: テスト環境の確認
- **デバッグ**: 基本的な HTTP 通信のテスト

## 実装詳細

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.get("/ping")
def ping():
    return JSONResponse({"message": "pong"}, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- **FastAPI**: Webフレームワーク
- **JSONResponse**: JSON形式でのレスポンス返却
- **uvicorn**: ASGI サーバー

## 拡張例

テスト機能を拡張する場合の例：

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.get("/ping")
def ping():
    return JSONResponse({"message": "pong"}, status_code=200)

@app.get("/status")
def status():
    return JSONResponse({"status": "running"}, status_code=200)

@app.post("/echo")
def echo(data: dict):
    return JSONResponse(data, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
