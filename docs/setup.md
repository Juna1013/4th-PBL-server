# セットアップガイド

このドキュメントでは、音声認識サーバーのローカル開発環境のセットアップ方法を説明します。

## 前提条件

- Python 3.10 以上
- pip
- git

## 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd server
```

## 2. 仮想環境の作成

### macOS/Linux

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

インストールには数分かかる場合があります（特にPyTorchが大きいため）。

## 4. サーバーの起動

### 方法1: 直接実行

```bash
python main.py
```

### 方法2: Uvicornを使用（開発時推奨）

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

`--reload` オプションを付けると、ファイルの変更時に自動的にサーバーが再起動します。

## 5. 動作確認

ブラウザで以下のURLにアクセスして、サーバーが正常に起動していることを確認します：

- http://localhost:8000 - トップページ
- http://localhost:8000/docs - Swagger UI（APIドキュメント）
- http://localhost:8000/health - ヘルスチェック

## トラブルシューティング

### ポートが既に使用されている

別のポート番号を指定してください：

```bash
uvicorn main:app --port 8080
```

### PyTorchのインストールが失敗する

CPUバージョンのPyTorchを使用してください：

```bash
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
```

### 依存関係のバージョン競合

仮想環境を削除して再作成してください：

```bash
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 環境変数

必要に応じて `.env` ファイルを作成して環境変数を設定できます：

```bash
# .env
PORT=8000
DEBUG=True
ALLOWED_ORIGINS=*
```

`.env` ファイルを使用する場合は、`python-dotenv` をインストールしてください：

```bash
pip install python-dotenv
```
