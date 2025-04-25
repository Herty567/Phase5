# experiment.py

import sys, os, csv, time, signal, subprocess

# ─── CONFIG ─────────────────────────────────────
RECV_SCRIPT   = "receiver.py"
SENDER_SCRIPT = "sender.py"
TIGER_IMG     = "tiger.jpg"
OUT_FILE      = "received_tiger.jpg"
PORT          = "5003"
IP            = "127.0.0.1"

# how long to wait for the receiver to bind
RECV_STARTUP  = 0.3

# if the sender never finishes, assume this max
MAX_DURATION  = 60.0
# ────────────────────────────────────────────────

def start_receiver(loss_rate: float):
    cmd = [
        sys.executable, RECV_SCRIPT,
        "--port", PORT,
        "--out_file", OUT_FILE,
        "--loss_rate", str(loss_rate)
    ]
    # on Windows we need CREATE_NEW_PROCESS_GROUP, on Unix setsid so killpg works
    if os.name == "nt":
        return subprocess.Popen(cmd,
                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        return subprocess.Popen(cmd,
                                preexec_fn=os.setsid,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_process(proc: subprocess.Popen):
    if proc.poll() is None:
        try:
            if os.name == "nt":
                proc.terminate()
            else:
                os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            proc.kill()
        proc.wait()

def run_sender(loss_rate: float, timeout: float, init_window: int) -> float:
    cmd = [
        sys.executable, SENDER_SCRIPT,
        "--ip",           IP,
        "--port",         PORT,
        "--file",         TIGER_IMG,
        "--loss_rate",    str(loss_rate),
        "--timeout",      str(timeout),
        "--init_window",  str(init_window)
    ]
    print(f"→ loss={loss_rate}, to={timeout}, win={init_window}")
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         text=True)

    try:
        out, _ = p.communicate(timeout=MAX_DURATION)
    except subprocess.TimeoutExpired:
        print(f"!! Sender timed out after {MAX_DURATION}s, killing…")
        p.kill()
        out, _ = p.communicate()
        return MAX_DURATION

    # scan for the “Data-transfer complete in X.XXXs”
    for line in reversed(out.splitlines()):
        if "Data-transfer complete in" in line:
            try:
                return float(line.split()[-1].rstrip("s"))
            except:
                break

    print("!! Could not parse duration; falling back to MAX_DURATION")
    return MAX_DURATION

def main():
    with open("phase5_perf.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["loss_rate","timeout","init_window","duration"])

        # 1) Sweep loss_rate 0%→70% by 10%
        for r in [i/100 for i in range(0,71,10)]:
            recv = start_receiver(r)
            time.sleep(RECV_STARTUP)
            dur = run_sender(r, 0.05, 1)
            stop_process(recv)
            writer.writerow([r, 0.05, 1, dur])

        # 2) Sweep timeout 10ms→100ms by 10ms
        for t in [i/1000 for i in range(10,101,10)]:
            recv = start_receiver(0.0)
            time.sleep(RECV_STARTUP)
            dur = run_sender(0.0, t, 1)
            stop_process(recv)
            writer.writerow([0.0, t, 1, dur])

        # 3) Sweep init_window 1→50 by 5
        for w in range(1,51,5):
            recv = start_receiver(0.0)
            time.sleep(RECV_STARTUP)
            dur = run_sender(0.0, 0.05, w)
            stop_process(recv)
            writer.writerow([0.0, 0.05, w, dur])

    print("✅ Done! Results in phase5_perf.csv")

if __name__ == "__main__":
    main()
