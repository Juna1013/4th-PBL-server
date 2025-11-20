# Raspberry Pi Pico W との統合ガイド

このドキュメントでは、Raspberry Pi Pico Wから音声認識サーバーを使用する方法を説明します。

## 概要

Raspberry Pi Pico Wでマイクから音声を録音し、WiFi経由でサーバーに送信して音声認識を行い、認識されたコマンドを受け取ってモーター制御などを行います。

## 必要なハードウェア

- Raspberry Pi Pico W
- マイクモジュール（例: MAX4466, INMP441など）
- WiFiネットワーク

## 配線例

### MAX4466マイクモジュールの場合

| MAX4466 | Pico W |
|---------|--------|
| VCC     | 3.3V   |
| GND     | GND    |
| OUT     | GP26 (ADC0) |

## MicroPythonのセットアップ

### 1. MicroPythonのインストール

1. [MicroPython公式サイト](https://micropython.org/download/RPI_PICO_W/)から最新のファームウェアをダウンロード
2. BOOTSELボタンを押しながらPico WをPCに接続
3. `.uf2` ファイルをPico Wのドライブにコピー

### 2. Thonnyの設定

1. Thonnyをインストール
2. 「ツール」→「オプション」→「インタープリター」
3. 「MicroPython (Raspberry Pi Pico)」を選択

## サンプルコード

### 完全な実装例

```python
from machine import Pin, ADC
import network
import urequests
import time
import array

# --- 設定 ---
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
SERVER_URL = "https://your-app.onrender.com"

# マイク設定
mic = ADC(Pin(26))

# モーター設定（ライントレースプログラムと同じピン）
LEFT_FWD_PIN = 5
LEFT_REV_PIN = 4
RIGHT_FWD_PIN = 2
RIGHT_REV_PIN = 3

from machine import PWM
left_fwd = PWM(Pin(LEFT_FWD_PIN))
left_rev = PWM(Pin(LEFT_REV_PIN))
right_fwd = PWM(Pin(RIGHT_FWD_PIN))
right_rev = PWM(Pin(RIGHT_REV_PIN))

for pwm in [left_fwd, left_rev, right_fwd, right_rev]:
    pwm.freq(1000)

# --- WiFi接続 ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"WiFi接続中: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        timeout = 10
        while timeout > 0 and not wlan.isconnected():
            time.sleep(1)
            timeout -= 1
    
    if wlan.isconnected():
        print("WiFi接続成功!")
        print("IP:", wlan.ifconfig()[0])
        return True
    else:
        print("WiFi接続失敗")
        return False

# --- 音声録音 ---
def record_audio(duration=2, sample_rate=16000):
    """
    マイクから音声を録音
    
    Args:
        duration: 録音時間（秒）
        sample_rate: サンプリングレート
    
    Returns:
        bytearray: WAV形式の音声データ
    """
    print(f"録音開始 ({duration}秒)...")
    
    num_samples = duration * sample_rate
    samples = array.array('H', [0] * num_samples)
    
    # サンプリング
    delay_us = int(1000000 / sample_rate)
    for i in range(num_samples):
        samples[i] = mic.read_u16()
        time.sleep_us(delay_us)
    
    print("録音完了")
    
    # WAVヘッダーを作成
    wav_data = create_wav(samples, sample_rate)
    return wav_data

def create_wav(samples, sample_rate):
    """
    サンプルデータからWAVファイルを作成
    """
    num_samples = len(samples)
    data_size = num_samples * 2  # 16bit = 2 bytes
    
    wav = bytearray()
    
    # RIFFヘッダー
    wav.extend(b'RIFF')
    wav.extend((data_size + 36).to_bytes(4, 'little'))
    wav.extend(b'WAVE')
    
    # fmtチャンク
    wav.extend(b'fmt ')
    wav.extend((16).to_bytes(4, 'little'))  # チャンクサイズ
    wav.extend((1).to_bytes(2, 'little'))   # PCM
    wav.extend((1).to_bytes(2, 'little'))   # モノラル
    wav.extend(sample_rate.to_bytes(4, 'little'))
    wav.extend((sample_rate * 2).to_bytes(4, 'little'))  # バイトレート
    wav.extend((2).to_bytes(2, 'little'))   # ブロックアライン
    wav.extend((16).to_bytes(2, 'little'))  # 16bit
    
    # dataチャンク
    wav.extend(b'data')
    wav.extend(data_size.to_bytes(4, 'little'))
    
    # 音声データ
    for sample in samples:
        wav.extend(sample.to_bytes(2, 'little'))
    
    return wav

# --- サーバー通信 ---
def send_audio_to_server(audio_data):
    """
    音声データをサーバーに送信して認識結果を取得
    """
    try:
        url = f"{SERVER_URL}/recognize"
        
        # マルチパートフォームデータ
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        
        body = bytearray()
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="audio"; filename="audio.wav"\r\n')
        body.extend(b'Content-Type: audio/wav\r\n\r\n')
        body.extend(audio_data)
        body.extend(f"\r\n--{boundary}--\r\n".encode())
        
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
        
        print("サーバーに送信中...")
        response = urequests.post(url, data=bytes(body), headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            response.close()
            print(f"認識成功: {result['command']}")
            return result['command']
        else:
            print(f"エラー: {response.status_code}")
            response.close()
            return None
    
    except Exception as e:
        print(f"送信エラー: {e}")
        return None

# --- モーター制御 ---
def execute_command(command):
    """
    認識されたコマンドに基づいてモーターを制御
    """
    BASE_PWM = 12500
    
    print(f"コマンド実行: {command}")
    
    if command == "前進":
        # 前進
        left_fwd.duty_u16(0)
        left_rev.duty_u16(BASE_PWM)
        right_fwd.duty_u16(BASE_PWM)
        right_rev.duty_u16(0)
        print("→ 前進")
    
    elif command == "後退":
        # 後退
        left_fwd.duty_u16(BASE_PWM)
        left_rev.duty_u16(0)
        right_fwd.duty_u16(0)
        right_rev.duty_u16(BASE_PWM)
        print("→ 後退")
    
    elif command == "左折":
        # 左折（その場回転）
        left_fwd.duty_u16(BASE_PWM)
        left_rev.duty_u16(0)
        right_fwd.duty_u16(BASE_PWM)
        right_rev.duty_u16(0)
        print("→ 左折")
    
    elif command == "右折":
        # 右折（その場回転）
        left_fwd.duty_u16(0)
        left_rev.duty_u16(BASE_PWM)
        right_fwd.duty_u16(0)
        right_rev.duty_u16(BASE_PWM)
        print("→ 右折")
    
    elif command == "停止":
        # 停止
        stop_motors()
        print("→ 停止")
    
    elif command == "スタート":
        # ライントレース開始（別のプログラムを呼び出すなど）
        print("→ ライントレース開始")
    
    else:
        print("→ 不明なコマンド")
        stop_motors()

def stop_motors():
    """全モーター停止"""
    left_fwd.duty_u16(0)
    left_rev.duty_u16(0)
    right_fwd.duty_u16(0)
    right_rev.duty_u16(0)

# --- メイン処理 ---
def main():
    """メインループ"""
    # WiFi接続
    if not connect_wifi():
        print("WiFi接続に失敗しました")
        return
    
    print("\n音声コマンド待機中...")
    print("ボタンを押して録音を開始")
    
    # ボタン（例: GP15）
    button = Pin(15, Pin.IN, Pin.PULL_UP)
    
    try:
        while True:
            # ボタンが押されたら録音開始
            if button.value() == 0:
                # 音声録音
                audio_data = record_audio(duration=2, sample_rate=16000)
                
                # サーバーに送信して認識
                command = send_audio_to_server(audio_data)
                
                # コマンド実行
                if command:
                    execute_command(command)
                    
                    # 一定時間動作（例: 2秒）
                    time.sleep(2)
                    
                    # 停止
                    stop_motors()
                
                # ボタンが離されるまで待つ
                while button.value() == 0:
                    time.sleep(0.1)
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n終了")
    
    finally:
        stop_motors()

if __name__ == "__main__":
    main()
```

## トラブルシューティング

### WiFiに接続できない

**原因:**
- SSID/パスワードが間違っている
- WiFiが2.4GHz帯ではない（Pico Wは5GHz非対応）

**解決策:**
- SSID/パスワードを確認
- 2.4GHz WiFiに接続

### 音声認識の精度が低い

**原因:**
- マイクの感度が低い
- ノイズが多い
- サンプリングレートが低い

**解決策:**
- マイクのゲインを調整
- 静かな環境で録音
- サンプリングレートを上げる（16000Hz推奨）

### メモリ不足エラー

**原因:**
- 録音時間が長すぎる
- サンプリングレートが高すぎる

**解決策:**
- 録音時間を短く（1〜2秒）
- サンプリングレートを下げる

## 改善案

### 1. 連続音声認識

ボタンを押さずに常に音声を監視：

```python
def detect_voice_activity():
    """音声アクティビティ検出"""
    threshold = 30000  # 調整が必要
    window = 100
    
    samples = [mic.read_u16() for _ in range(window)]
    energy = sum(abs(s - 32768) for s in samples)
    
    return energy > threshold * window
```

### 2. オフライン音声認識

軽量な音声認識をPico W上で実行（精度は低い）：

```python
# TensorFlow Lite Microを使用
# 詳細は省略
```

### 3. バッテリー駆動

WiFi接続を必要な時だけ有効にして省電力化：

```python
wlan.active(False)  # WiFiオフ
# ...
wlan.active(True)   # WiFiオン（送信時のみ）
```
