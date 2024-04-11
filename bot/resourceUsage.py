import time

import psutil


def displayusage(cpu_usage,memory_usage,bars=50):
    cpu_percent=(cpu_usage/100)
    cpu_bar="*" * int(cpu_percent * bars) +'-'*(bars - int(cpu_percent* bars))
    mem_percent=memory_usage/100
    mem_bar="*" * int(mem_percent * bars) +'-'*(bars - int(mem_percent* bars))
    print(f"\rCPU Usage: |{cpu_bar}| {cpu_usage:.2f}%  ",end="")
    print(f"MEM Usage: |{mem_bar}| {memory_usage:.2f}%  ",end="\r")
def visulaizer():
    while True:
        displayusage(psutil.cpu_percent(),psutil.virtual_memory().percent,30)
        time.sleep(0.4)
