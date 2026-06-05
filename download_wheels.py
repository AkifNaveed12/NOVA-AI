import urllib.request
import os
import sys
import time
import subprocess

urls = {
    "tensorflow_intel-2.16.1-cp311-cp311-win_amd64.whl": "https://files.pythonhosted.org/packages/e0/36/6278e4e7e69a90c00e0f82944d8f2713dd85a69d1add455d9e50446837ab/tensorflow_intel-2.16.1-cp311-cp311-win_amd64.whl",
    "tf_keras-2.16.0-py3-none-any.whl": "https://files.pythonhosted.org/packages/75/aa/cf09f8956d4f276f655b13674e15d8d6015fd832f9689aa9ff2a515781ab/tf_keras-2.16.0-py3-none-any.whl",
    "deepface-0.0.93-py3-none-any.whl": "https://files.pythonhosted.org/packages/ca/f6/4fa3f64b1a02141c037ed71a40ebf8fb8cc1ec9e860df6301fc9121bc0d4/deepface-0.0.93-py3-none-any.whl"
}

dest_dir = r"D:\wheels"
os.makedirs(dest_dir, exist_ok=True)

log_file = r"D:\wheels_download.log"

def main():
    with open(log_file, "w") as log:
        log.write("Starting wheel downloads...\n")
        log.flush()
        
        for filename, url in urls.items():
            dest_path = os.path.join(dest_dir, filename)
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                # If file exists, check size
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    with urllib.request.urlopen(req) as response:
                        total_size = int(response.info().get('Content-Length', 0))
                    if os.path.getsize(dest_path) == total_size:
                        log.write(f"{filename} already fully downloaded. Skipping.\n")
                        log.flush()
                        continue
                except Exception:
                    pass
                
            log.write(f"Downloading {filename} from {url}...\n")
            log.flush()
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    total_size = int(response.info().get('Content-Length', 0))
                    downloaded = 0
                    block_size = 1024 * 1024 # 1 MB
                    
                    with open(dest_path, 'wb') as f:
                        while True:
                            buffer = response.read(block_size)
                            if not buffer:
                                break
                            f.write(buffer)
                            downloaded += len(buffer)
                            percent = (downloaded / total_size) * 100 if total_size else 0
                            log.write(f"Downloaded {downloaded / (1024*1024):.2f}MB / {total_size / (1024*1024):.2f}MB ({percent:.1f}%)\n")
                            log.flush()
                log.write(f"Finished downloading {filename}\n")
                log.flush()
            except Exception as e:
                log.write(f"Error downloading {filename}: {e}\n")
                log.flush()
                
        log.write("All downloads finished!\n")
        log.flush()

if __name__ == "__main__":
    main()
