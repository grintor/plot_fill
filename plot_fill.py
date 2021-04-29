import subprocess
import threading
import os
import time
from datetime import datetime
import psutil
from glob import glob
import sys
import atexit

try:
    plot_size = sys.argv[1]
    tmp_drive = sys.argv[2]
    dest_drive = sys.argv[3]
except:
    print(f"usage: {sys.argv[0]} k_size tmp_drive dest_drive")
    print(f"eg: {sys.argv[0]} 25 c c")
    os._exit(-3)

total_log_lines = 2630
k_map = {
    '25': {
        'mem_mb': 1389,
        'tmp_bytes': 139,
        'dest_bytes': 0.9
    },
    '32': {
        'mem_mb': 3389,
        'tmp_bytes': 256624295936,
        'dest_bytes': 108877420954
    },
    '33': {
        'mem_mb': 7400,
        'tmp_bytes': 549755813888,
        'dest_bytes': 224197292852
    },
    '34': {
        'mem_mb': 14800,
        'tmp_bytes': 1117765238784,
        'dest_bytes': 461494235956
    },
    '35': {
        'mem_mb': 29600,
        'tmp_bytes': 2335388467200,
        'dest_bytes': 949295146599
    },
}

while True:
    tmp_drv = psutil.disk_usage(f'{tmp_drive}:\\')
    dest_drv = psutil.disk_usage(f'{dest_drive}:\\')
    
    if tmp_drv.free < k_map[plot_size]['tmp_bytes']:
        print('Not enough space on the tmp drive to continue')
        break
    if dest_drv.free < k_map[plot_size]['dest_bytes']:
        print('Not enough space on the dest drive to continue')
        break
    
    mem_mb = k_map[plot_size]['mem_mb']
    log_lines = 0
    epoch_start = int(time.time())
    os.chdir(glob(os.environ['localappdata'] + r'\chia-blockchain\app-*\resources\app.asar.unpacked\daemon')[-1])
    chia_proc = subprocess.Popen(
        [   'chia.exe',
            'plots',
            'create',
            f'-k{plot_size}',
            '-n1', f'-t{tmp_drive}:\\tmp',
            f'-2{tmp_drive}:\\tmp',
            f'-d{dest_drive}:\\',
            f'-b{mem_mb}',
            '-u128',
            '-r2',
            '--override-k'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    atexit.register(chia_proc.kill)
    
    print(f"started plot creation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({epoch_start})")
    print(f"process pid: {chia_proc.pid}")
    print(f"plot is of size: k{plot_size}")
    print(f"temp dir: {tmp_drive}:\\tmp")
    print(f"dest dir: {dest_drive}:\\")

    p = psutil.Process(chia_proc.pid)
    p.ionice(psutil.IOPRIO_VERYLOW)
    p.nice(psutil.IDLE_PRIORITY_CLASS)

    print(f"The plotting process CPU and I/O Priority have been lowered")

    while chia_proc.poll() == None:
        log_lines += 1
        progress = format(log_lines/total_log_lines*100, '.2f')
        print('\b\b\b\b\b\b\b', end='', flush=True)
        print(f"{progress}%", end='', flush=True)
        out_line = chia_proc.stdout.readline().decode()
        with open(f'{dest_drive}:\\{epoch_start}.log','a') as log:
            try:
                log.write(out_line)
            except:
                pass
    print(f"\nfinished plot creation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ({round((int(time.time()) - epoch_start)/60/60, 2)} hours)")
    print('\n\n')
    time.sleep(60) # just in case something goes wrong, don't want a million log files


#input('press enter to exit... ')
