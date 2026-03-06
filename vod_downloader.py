import os
import time
import requests
import m3u8
import subprocess
from config import config

CHECK_INTERVAL = 10  # 每10秒抓一次新片段

def get_m3u8_playlist_url(vod_url):
    import streamlink
    from streamlink.options import Options
    from twitch_token import token

    session = streamlink.Streamlink()
    options = Options()
    
    # 取得訂閱者的網頁 Token
    auth_token = token.get('auth_token')
    if not auth_token:
        raise ValueError("請在 twitch_token.json 中設定 auth_token")
        
    # 帶入訂閱者 Token 以取得觀看權限
    options.set("api-header", [("Authorization", f"OAuth {auth_token}")])
    
    streams = session.streams(vod_url, options)
    
    # 提早報錯防呆
    if not streams:
        raise RuntimeError("無法取得串流：可能是 Token 無效、沒有訂閱該頻道，或影片不存在。")
        
    return streams['best'].url

def download_ts_segment(segment_url, save_path):
    if os.path.exists(save_path):
        return False
    r = requests.get(segment_url, stream=True)
    if r.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"下載片段: {os.path.basename(save_path)}")
        return True
    else:
        print(f"下載失敗: {segment_url}")
        return False

def merge_ts_files(input_folder, output_file):
    """
    合併指定資料夾中的連續 ts 檔案為一個影片。
    Args:
        input_folder (str): 儲存 ts 檔案的資料夾路徑
        output_file (str): 合併後影片輸出路徑（建議為 .ts 或 .mp4）
    """
    # 取得所有 ts 檔並依照數字順序排序
    ts_files = sorted(
        [f for f in os.listdir(input_folder) if f.endswith(".ts")],
        key=lambda x: int(os.path.splitext(x)[0])
    )

    # 建立 ffmpeg 所需的輸入清單檔案（使用絕對路徑 + 正斜線）
    list_file_path = os.path.join(input_folder, "file_list.txt")
    with open(list_file_path, "w", encoding="utf-8") as f:
        for ts in ts_files:
            abs_path = os.path.abspath(os.path.join(input_folder, ts))
            unix_path = abs_path.replace("\\", "/")  # 替換為 ffmpeg 可讀格式
            f.write(f"file '{unix_path}'\n")

    # 使用 ffmpeg 合併檔案
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file_path,
        "-c", "copy", output_file
    ]

    subprocess.run(cmd, check=True)
    os.remove(list_file_path)  # 合併後刪除暫存清單
    print(f"✅ 合併完成：{output_file}")

def main():
    vod_url = config["vod_url"]
    vod_id = config["vod_id"]
    output_dir = os.path.join("vod", vod_id)
    os.makedirs(output_dir, exist_ok=True)

    m3u8_url = get_m3u8_playlist_url(vod_url)
    downloaded_segments = set()

    while True:

        try:
            m3u8_obj = m3u8.load(m3u8_url)

            new_segments = []
            for seg in m3u8_obj.segments:
                filename = os.path.basename(seg.uri)
                if filename not in downloaded_segments:
                    new_segments.append(seg)

            if new_segments:
                for seg in new_segments:
                    segment_url = seg.absolute_uri
                    filename = os.path.basename(segment_url)
                    save_path = os.path.join(output_dir, filename)
                    if download_ts_segment(segment_url, save_path):
                        downloaded_segments.add(filename)
            else:
                print("目前無新片段")

            if m3u8_obj.is_endlist:
                print("✅ 偵測到直播結束")
                output_file = os.path.join(config["save_file"], f"{vod_id}.mp4")
                merge_ts_files(output_dir, output_file)
                break

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"⚠️ 錯誤: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
