import subprocess


process = subprocess.Popen("python3 bot.py", stdin=subprocess.PIPE, stdout=subprocess.PIPE)

while True:
    for line in process.stdout:
        line = str(line).lower()
        if "heartbeat blocked" in line:
            process.terminate()
            print("\n\n")
            process = subprocess.Popen("python3 bot.py", stdin=subprocess.PIPE, stdout=subprocess.PIPE)