# デプロイガイド

このドキュメントでは、音声認識サーバーをRenderにデプロイする手順を説明します。

## Renderとは

[Render](https://render.com)は、Webアプリケーションを簡単にデプロイできるクラウドプラットフォームです。GitHubリポジトリと連携して、自動デプロイが可能です。

## デプロイの前提条件

- GitHubアカウント
- Renderアカウント（無料プランで可）
- コードがGitHubにプッシュされていること

## デプロイ手順

### 1. GitHubにコードをプッシュ

```bash
cd /Users/juna1013/bin/4th-PBL/server
git add .
git commit -m "Add voice recognition server"
git push origin main
```

### 2. Renderにログイン

1. [Render](https://render.com)にアクセス
2. GitHubアカウントでサインイン

### 3. 新しいWeb Serviceを作成

1. ダッシュボードで「New +」をクリック
2. 「Web Service」を選択
3. GitHubリポジトリを接続
4. リポジトリを選択

### 4. サービスの設定

以下の項目を設定します：

**基本設定:**
- **Name:** `voice-recognition-server`（任意の名前）
- **Region:** `Singapore`（日本から最も近いリージョン）
- **Branch:** `main`
- **Root Directory:** `server`（リポジトリのルートがserverディレクトリでない場合）

**Build & Deploy設定:**
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**インスタンスタイプ:**
- **Free**（無料プラン）または **Starter**（有料プラン）

### 5. 環境変数の設定（オプション）

必要に応じて環境変数を追加：

| キー | 値 |
|------|-----|
| `PYTHON_VERSION` | `3.11.0` |
| `DEBUG` | `False` |

### 6. デプロイ

「Create Web Service」をクリックすると、自動的にデプロイが開始されます。

初回デプロイには5〜10分程度かかります。

### 7. デプロイ完了の確認

デプロイが完了すると、以下のようなURLが発行されます：

```
https://your-app-name.onrender.com
```

ブラウザでアクセスして動作を確認：
```
https://your-app-name.onrender.com/health
```

レスポンス例:
```json
{
  "status": "healthy",
  "message": "Server is running"
}
```

---

## 自動デプロイの設定

### render.yaml を使用

プロジェクトに `render.yaml` が含まれているため、Renderは自動的にこの設定を読み込みます。

`render.yaml` の内容:
```yaml
services:
  - type: web
    name: voice-recognition-server
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### 自動デプロイの有効化

1. Renderダッシュボードで「Settings」を開く
2. 「Auto-Deploy」セクションで「Yes」を選択
3. mainブランチにプッシュすると自動的にデプロイされます

---

## カスタムドメインの設定

Renderでは無料プランでもカスタムドメインを設定できます。

1. Renderダッシュボードで「Settings」を開く
2. 「Custom Domain」セクションで「Add Custom Domain」をクリック
3. ドメイン名を入力（例: `api.yourdomain.com`）
4. DNS設定で CNAMEレコードを追加

---

## デプロイ後の確認事項

### 1. ヘルスチェック

```bash
curl https://your-app-name.onrender.com/health
```

### 2. APIドキュメント

ブラウザで以下にアクセス：
```
https://your-app-name.onrender.com/docs
```

### 3. ログの確認

Renderダッシュボードの「Logs」タブでサーバーログを確認できます。

---

## トラブルシューティング

### デプロイが失敗する

**原因1: requirements.txtの依存関係エラー**
- ログを確認して、どのパッケージでエラーが発生しているか確認
- 必要に応じてバージョンを調整

**原因2: ビルドタイムアウト**
- Renderの無料プランではビルド時間に制限があります
- 不要な依存関係を削除するか、有料プランにアップグレード

### アプリが応答しない

**原因1: スリープモード**
- 無料プランでは15分間リクエストがないとスリープします
- 初回アクセス時に起動するため、数秒〜数十秒かかります

**原因2: ポート番号の設定**
- 環境変数 `$PORT` を使用していることを確認
- Start Commandが正しいか確認

### メモリ不足

無料プランは512MBのメモリ制限があります。PyTorchのような大きなライブラリを使用する場合は、有料プランを検討してください。

---

## パフォーマンス最適化

### 1. 軽量なPyTorchを使用

CPU版のPyTorchを使用してサイズを削減：

```txt
# requirements.txt
torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
```

### 2. 不要な依存関係を削除

開発時のみ必要なパッケージは除外してください。

### 3. キャッシュの活用

Renderは依存関係をキャッシュするため、2回目以降のデプロイは高速になります。

---

## モニタリング

### Renderのダッシュボード

- CPU使用率
- メモリ使用率
- リクエスト数
- レスポンスタイム

これらの情報はRenderダッシュボードで確認できます。

### 外部モニタリングツール

本番環境では以下のツールの使用を検討：
- **Sentry** - エラー追跡
- **Datadog** - パフォーマンスモニタリング
- **Uptime Robot** - ダウンタイム監視

---

## セキュリティ

### 1. HTTPS

Renderは自動的にHTTPSを有効にします。

### 2. 環境変数

機密情報は環境変数として設定し、コードにハードコードしないでください。

### 3. CORS設定

本番環境では適切なCORS設定を行ってください：

```python
allow_origins=["https://your-frontend-domain.com"]
```

### 4. レート制限

悪意のあるリクエストを防ぐため、レート制限の実装を検討してください。
