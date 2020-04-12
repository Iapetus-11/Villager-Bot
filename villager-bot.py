import subprocess

while True:
    p = subprocess.Popen("python3 bot.py", stdout=subprocess.PIPE, shell=True)
    for line in p.stdout:
        print(line)
        if "heartbeat" in line.lower():
            break
    print("== BOT EXITED ==")
    p.terminate()