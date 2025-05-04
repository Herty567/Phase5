import socket
import struct
import time
import threading
import random
import csv
import argparse
import sys

EOF_SEQ = 0xFFFFFFFF
SYN     = 1
SYN_ACK = 2
ACK     = 3

class Sender:
    def __init__(self, args):
        self.addr        = (args.ip, args.port)
        self.file_path   = args.file
        self.error_rate  = args.error_rate
        self.loss_rate   = args.loss_rate

        self.timeout     = args.timeout
        self.init_window = args.init_window
        self.ssthresh    = args.ssthresh

        self.base     = 0
        self.next_seq = 0
        self.buffer   = {}
        self.timer    = None
        self.lock     = threading.Lock()

        self.cwnd       = self.init_window
        self.rtt        = 0.0
        self.rto        = args.timeout
        self.send_times = {}

        self.start_time = None
        self.log_t      = []
        self.log_cwnd   = []
        self.log_rtt    = []
        self.log_rto    = []

    @staticmethod
    def compute_checksum(data: bytes) -> int:
        s = 0
        for i in range(0, len(data), 2):
            w = (data[i] << 8) + (data[i+1] if i+1 < len(data) else 0)
            s = (s + w) & 0xFFFF
        return s

    def make_packets(self):
        seq = 0
        with open(self.file_path, "rb") as f:
            while chunk := f.read(1024):
                pkt   = struct.pack("!I", seq) + chunk
                cksum = self.compute_checksum(pkt)
                full  = struct.pack("!H", cksum) + pkt
                self.buffer[seq] = full
                seq += 1
        self.total = seq

    def start_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.rto, self.timeout_handler)
        self.timer.start()

    def timeout_handler(self):
        with self.lock:
            print(f"[S] Timeout -> resend from {self.base}")
            self.start_timer()
            for s in range(self.base, min(self.next_seq, self.base + self.cwnd)):
                self.sock.sendto(self.buffer[s], self.addr)
                self.send_times[s] = time.time()

    def log_state(self):
        t = time.time() - self.start_time
        self.log_t.append(t)
        self.log_cwnd.append(self.cwnd)
        self.log_rtt.append(self.rtt)
        self.log_rto.append(self.rto)

    def send_file(self):
        self.make_packets()

        # 1) 3-way handshake
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1.0)
        while True:
            self.sock.sendto(struct.pack("!I", SYN), self.addr)
            print("[S] -> SYN")
            try:
                data, _ = self.sock.recvfrom(4)
                if struct.unpack("!I", data)[0] == SYN_ACK:
                    print("[S] <- SYN-ACK")
                    break
            except socket.timeout:
                print("[S] (handshake) SYN timeout, retrying")

        self.sock.sendto(struct.pack("!I", ACK), self.addr)
        print("[S] -> ACK")

        # 2) data transfer
        self.start_time = time.time()
        self.start_timer()

        while True:
            with self.lock:
                while self.next_seq < self.base + self.cwnd and self.next_seq < self.total:
                    seq = self.next_seq
                    self.sock.sendto(self.buffer[seq], self.addr)
                    self.send_times[seq] = time.time()
                    print(f"[S] -> pkt#{seq}")
                    self.next_seq += 1

            try:
                ackpkt, _ = self.sock.recvfrom(4)
                ack = struct.unpack("!I", ackpkt)[0]
            except socket.timeout:
                continue

            if random.random() < self.loss_rate:
                print("[S] (sim) ACK loss")
                continue

            with self.lock:
                if ack >= self.base:
                    sample = time.time() - self.send_times.get(ack, time.time())
                    # EWMA RTT/RTO
                    self.rtt = (1-0.125)*self.rtt + 0.125*sample
                    self.rto = max(0.001, self.rtt + 4*0.25*abs(sample-self.rtt))

                    self.base = ack + 1
                    print(f"[S] <- ACK#{ack}  base->{self.base}  sampleRTT={sample:.3f}s  RTO={self.rto:.3f}s")
                    self.log_state()

                    self.timer.cancel()
                    self.start_timer()

                    # congestion control
                    if self.cwnd < self.ssthresh:
                        self.cwnd *= 2
                    else:
                        self.cwnd += 1

                    # done?
                    if self.base == self.total:
                        duration = time.time() - self.start_time
                        print(f"[S] Data-transfer complete in {duration:.3f}s")
                        self.timer.cancel()
                        break

        self.sock.close()
        # dump timeseries
        with open("tcp_timeseries.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time","cwnd","rtt","rto"])
            for t,c,r,x in zip(self.log_t, self.log_cwnd, self.log_rtt, self.log_rto):
                w.writerow([t,c,r,x])

        return duration

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ip",          default="127.0.0.1")
    p.add_argument("--port",        type=int,   default=5003)
    p.add_argument("--file",        default="tiger.jpg")
    p.add_argument("--error_rate",  type=float, default=0.0)
    p.add_argument("--loss_rate",   type=float, default=0.0)
    p.add_argument("--timeout",     type=float, default=0.05)
    p.add_argument("--init_window", type=int,   default=1)
    p.add_argument("--ssthresh",    type=int,   default=64)
    args = p.parse_args()

    sender = Sender(args)
    try:
        dur = sender.send_file()
    except Exception as e:
        print("Sender crashed (unexpected):", e)
        sys.exit(1)

    # record duration for experiment.py
    with open("completion_times.csv", "a", newline="") as f:
        csv.writer(f).writerow([args.loss_rate, args.timeout, args.init_window, dur])
    sys.exit(0)