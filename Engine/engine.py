import subprocess

engine = subprocess.Popen(
    ['./kingfish/kingfish_engine'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    universal_newlines=True,
    bufsize=1
)

def send_cmd(cmd):
    engine.stdin.write(cmd + '\n')
    engine.stdin.flush()

def get_response():
    while True:
        line = engine.stdout.readline()
        print("ENGINE:", line.strip())
        if "bestmove" in line or line.strip() == "uciok":
            break

# Giao tiếp mẫu
send_cmd("uci")
get_response()

send_cmd("isready")
get_response()

send_cmd("position startpos moves e2e4")
send_cmd("go")
get_response()
