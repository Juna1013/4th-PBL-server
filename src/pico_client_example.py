"""
Raspberry Pi Pico W用のサンプルクライアントコード

このスクリプトは、Raspberry Pi Pico Wから
FastAPI音声認識サーバーに音声データを送信する例です。
"""

import network
import urequests
import time
import json

# WiFi設定
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# サーバー設定
SERVER_URL = "https://your-app.onrender.com"  # Renderのデプロイ後のURL
# ローカルテスト用: "http://192.168.1.100:8000"

def connect_wifi():
    """WiFiに接続"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"WiFi接続中: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # 接続待機
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            print("接続待機中...")
            time.sleep(1)
    
    if wlan.isconnected():
        print("WiFi接続成功!")
        print("IP:", wlan.ifconfig()[0])
        return True
    else:
        print("WiFi接続失敗")
        return False

def check_server_health():
    """サーバーのヘルスチェック"""
    try:
        url = f"{SERVER_URL}/health"
        response = urequests.get(url)
        data = response.json()
        response.close()
        
        print(f"サーバー状態: {data['status']}")
        return data['status'] == 'healthy'
    except Exception as e:
        print(f"ヘルスチェック失敗: {e}")
        return False

def get_supported_commands():
    """サポートされているコマンド一覧を取得"""
    try:
        url = f"{SERVER_URL}/commands"
        response = urequests.get(url)
        data = response.json()
        response.close()
        
        print(f"サポートコマンド: {data['commands']}")
        return data['commands']
    except Exception as e:
        print(f"コマンド取得失敗: {e}")
        return []

def send_audio(audio_data, filename="audio.wav"):
    """
    音声データをサーバーに送信してコマンドを取得
    
    Args:
        audio_data: 音声データ（バイト列）
        filename: ファイル名
        
    Returns:
        dict: サーバーからのレスポンス
    """
    try:
        url = f"{SERVER_URL}/recognize"
        
        # マルチパートフォームデータの作成
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="audio"; filename="{filename}"\r\n'
            f"Content-Type: audio/wav\r\n\r\n"
        ).encode()
        
        body += audio_data
        body += f"\r\n--{boundary}--\r\n".encode()
        
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
        
        print("音声データ送信中...")
        response = urequests.post(url, data=body, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            response.close()
            
            print(f"認識成功: {result['command']} (信頼度: {result['confidence']})")
            return result
        else:
            print(f"エラー: {response.status_code}")
            response.close()
            return None
            
    except Exception as e:
        print(f"音声送信失敗: {e}")
        return None

def main():
    """メイン処理"""
    # WiFi接続
    if not connect_wifi():
        print("WiFi接続できませんでした")
        return
    
    # サーバーヘルスチェック
    if not check_server_health():
        print("サーバーに接続できません")
        return
    
    # サポートコマンド取得
    commands = get_supported_commands()
    
    # テスト用: ダミー音声データを送信
    # 実際には、マイクから録音した音声データを使用してください
    print("\nテスト送信...")
    
    # 例: 簡単なWAVヘッダーとダミーデータ
    # 実際のマイク録音処理に置き換えてください
    dummy_audio = create_dummy_wav()
    
    result = send_audio(dummy_audio)
    
    if result and result['success']:
        command = result['command']
        print(f"\n受信コマンド: {command}")
        
        # コマンドに応じた処理
        execute_command(command)

def create_dummy_wav():
    """
    テスト用のダミーWAVファイルを作成
    実際にはマイクから録音した音声を使用してください
    """
    # 簡単なWAVヘッダー（16bit, 16kHz, モノラル）
    sample_rate = 16000
    num_samples = 16000  # 1秒分
    
    wav_header = bytearray([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x00, 0x00, 0x00, 0x00,  # ファイルサイズ（後で計算）
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # fmtチャンクサイズ
        0x01, 0x00,              # フォーマット（PCM）
        0x01, 0x00,              # チャンネル数（モノラル）
        0x80, 0x3E, 0x00, 0x00,  # サンプルレート（16000）
        0x00, 0x7D, 0x00, 0x00,  # バイトレート
        0x02, 0x00,              # ブロックアライン
        0x10, 0x00,              # ビット深度（16bit）
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # データサイズ（後で計算）
    ])
    
    # ダミーの音声データ（サイン波）
    import math
    audio_data = bytearray()
    for i in range(num_samples):
        # 440Hzのサイン波
        sample = int(5000 * math.sin(2 * math.pi * 440 * i / sample_rate))
        # 16bitリトルエンディアン
        audio_data.append(sample & 0xFF)
        audio_data.append((sample >> 8) & 0xFF)
    
    return bytes(wav_header + audio_data)

def execute_command(command):
    """
    受信したコマンドを実行
    
    Args:
        command: 実行するコマンド文字列
    """
    print(f"コマンド実行: {command}")
    
    # ここでモーター制御などの実装を追加
    if command == "前進":
        print("→ モーターを前進させる")
        # モーター制御コード
    elif command == "後退":
        print("→ モーターを後退させる")
    elif command == "左折":
        print("→ 左に曲がる")
    elif command == "右折":
        print("→ 右に曲がる")
    elif command == "停止":
        print("→ モーターを停止")
    elif command == "スタート":
        print("→ 走行開始")
    else:
        print("→ 不明なコマンド")

if __name__ == "__main__":
    main()
