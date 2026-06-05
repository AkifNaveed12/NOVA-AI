import os
import sys
import time
import requests

url = "https://files.pythonhosted.org/packages/e0/36/6278e4e7e69a90c00e0f82944d8f2713dd85a69d1add455d9e50446837ab/tensorflow_intel-2.16.1-cp311-cp311-win_amd64.whl"
dest = "D:\\tensorflow_intel-2.16.1-cp311-cp311-win_amd64.whl"
log_path = "D:\\tf_download_manual.log"

def log(msg):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{timestamp}] {msg}\n"
    print(line, end="")
    try:
        with open(log_path, "a") as f:
            f.write(line)
    except Exception:
        pass

# Ensure any existing log is cleared
if os.path.exists(log_path):
    try:
        os.remove(log_path)
    except Exception:
        pass

log("Starting manual download of TensorFlow Intel wheel...")
try:
    headers = {"User-Agent": "pip/26.1.1"}
    r = requests.get(url, headers=headers, stream=True, timeout=30)
    r.raise_for_status()
    total_size = int(r.headers.get('content-length', 0))
    log(f"Content-Length: {total_size} bytes ({total_size / (1024*1024):.2f} MB)")
    
    downloaded = 0
    start_time = time.time()
    last_log_time = time.time()
    
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):  # 1MB chunks
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                current_time = time.time()
                if current_time - last_log_time >= 3 or downloaded == total_size:
                    elapsed = current_time - start_time
                    speed = (downloaded / (1024*1024)) / elapsed if elapsed > 0 else 0
                    percent = (downloaded / total_size) * 100 if total_size > 0 else 0
                    log(f"Downloaded {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB ({percent:.1f}%) | Speed: {speed:.2f} MB/s")
                    last_log_time = current_time
                    
    log("Download completed successfully!")
except Exception as e:
    log(f"Download failed: {e}")
