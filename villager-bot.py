import subprocess

while True:
    p = subprocess.Popen("python3 bot.py", stderr=subprocess.PIPE, shell=True)
    for line in p.stderr:
        print(line.decode("utf-8").rstrip("\n"))
        if "heartbeat blocked" in line.decode("utf-8").lower():
            break
    print("== BOT EXITED ==")
    p.terminate()