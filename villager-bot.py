import subprocess

while True:
    p = subprocess.Popen("python3 bot.py", stdout=subprocess.PIPE, shell=True)
    stop = False
    while not stop:
        for line in p.stdout:
            print(line)
            if "heartbeat" in line.lower():
                stop = True
                break
    print("== BOT EXITED ==")
    p.terminate()