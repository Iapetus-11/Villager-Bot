import subprocess

while True:
    p = subprocess.Popen("./villager-bot.sh", stdout=subprocess.PIPE)
    for line in p.stdout:
        print(line)
        if "blocked" in line.lower():
            break
    print("== BOT EXITED ==")
    p.terminate()