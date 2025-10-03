# 音声認識機能 - 使用方法

## 概要
音声コマンド（go, right, left, stop）を認識してライントレースカーを制御する機能です。

## APIエンドポイント

### 1. 音声認識実行
```
POST /api/speech/predict
Content-Type: multipart/form-data
```

**パラメータ:**
- `audio_file`: 音声ファイル（WAV, MP3など）
- `confidence_threshold`: 信頼度閾値（デフォルト: 0.7）
- `auto_execute`: 自動実行フラグ（デフォルト: false）

**レスポンス例:**
```json
{
  "success": true,
  "predicted_command": "go",
  "confidence": 0.89,
  "is_confident": true,
  "all_predictions": [
    {"command": "go", "confidence": 0.89},
    {"command": "stop", "confidence": 0.06},
    {"command": "right", "confidence": 0.03},
    {"command": "left", "confidence": 0.02}
  ],
  "auto_executed": false,
  "timestamp": "2024-01-01T12:00:00"
}
```

### 2. モデル情報取得
```
GET /api/speech/model/info
```

### 3. サポートコマンド一覧
```
GET /api/speech/commands
```

## 音声録音の推奨事項

1. **録音環境**: 静かな環境で録音
2. **録音時間**: 1秒程度の明瞭な発話
3. **音声品質**: 16kHzサンプリングレート推奨
4. **コマンド**: "go", "right", "left", "stop" を明確に発音

## curl使用例

```bash
# 音声ファイルをアップロードして認識
curl -X POST "http://localhost:8000/api/speech/predict" \
  -F "audio_file=@command.wav" \
  -F "auto_execute=true"

# モデル情報を取得
curl "http://localhost:8000/api/speech/model/info"
```

## フロントエンド連携

```javascript
// 音声認識の実行
const formData = new FormData();
formData.append('audio_file', audioBlob, 'command.wav');
formData.append('auto_execute', 'true');

fetch('/api/speech/predict', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('予測結果:', data.predicted_command);
  console.log('信頼度:', data.confidence);
});
```

## トラブルシューティング

### よくある問題

1. **モデルが読み込めない**
   - TensorFlowバージョンの互換性問題
   - 解決策: 互換モデル（.kerasフォーマット）を使用

2. **音声認識精度が低い**
   - 背景ノイズの影響
   - 録音品質の問題
   - 解決策: 静かな環境で明瞭に発話

3. **ファイルアップロードエラー**
   - ファイルサイズ制限（10MB）
   - サポートされていないフォーマット
   - 解決策: WAVまたはMP3形式を使用

### ログ確認

```bash
# サーバーログで音声認識の詳細を確認
tail -f server.log | grep "speech_recognition"
```

## デプロイ時の注意点

1. **Renderでのデプロイ**
   - ML依存関係のビルド時間が長い
   - メモリ使用量の増加に注意

2. **モデルファイル**
   - `models/speech_cnn_compatible.keras` を使用
   - 元の .h5 ファイルはバージョン互換性に問題あり

3. **パフォーマンス**
   - 初回予測時は読み込み時間がかかる
   - 継続的な使用では高速化される