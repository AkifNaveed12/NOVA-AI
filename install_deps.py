import subprocess
import sys
import os
import time

env = os.environ.copy()
env['TEMP'] = r'D:\pip-tmp'
env['TMP'] = r'D:\pip-tmp'
env['TMPDIR'] = r'D:\pip-tmp'

log_path = r'D:\pip_install.log'
with open(log_path, 'w', encoding='utf-8') as log_file:
    log_file.write("Starting installation...\n")
    log_file.flush()

    # Run pip install in a detached process
    p = subprocess.Popen([
        sys.executable, '-m', 'pip', 'install',
        'tensorflow-cpu==2.16.1', 'tf-keras==2.16.0', 'deepface==0.0.93',
        '--cache-dir', r'D:\pip-cache'
    ], env=env, stdout=log_file, stderr=log_file, creationflags=0x00000008) # DETACHED_PROCESS

print("Detached process started. PID:", p.pid)
