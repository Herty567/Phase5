import socket
import struct
import random
import argparse

PACKET_SIZE = 1024
EOF_SEQ     = 0xFFFFFFFF
SYN         = 1
SYN_ACK     = 2
ACK         = 3
FIN         = 4
IDLE_TIMEOUT= 60.0  # seconds of no data → abort

class Receiver:
    def __init__(self, args):
        self.err      = args.error_rate
        self.loss     = args.loss_rate
        self.port     = args.port
        self.out_file = args.out_file

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", self.port))
        print(f"[R] Listening on UDP/{self.port}...")

    def corrupt(self, data: bytes) -> bytes:
        if random.random() < self.err:
            b = bytearray(data)
            b[0] ^= 1
            print("[R] (sim) data corrupt")
            return bytes(b)
        return data

    @staticmethod
    def checksum(data: bytes) -> int:
        s = 0
        for i in range(0, len(data), 2):
            w = (data[i] << 8) + (data[i+1] if i+1 < len(data) else 0)
            s = (s + w) & 0xFFFF
        return s

    def serve(self):
        while True:
            expected = 0

            # 3-way handshake
            self.sock.settimeout(None)
            data, addr = self.sock.recvfrom(4)
            if struct.unpack("!I", data)[0] != SYN:
                continue
            self.sock.sendto(struct.pack("!I", SYN_ACK), addr)
            print("[R] -> SYN-ACK")
            data, _ = self.sock.recvfrom(4)
            if struct.unpack("!I", data)[0] != ACK:
                continue
            print("[R] <- ACK (handshake done)")

            # data transfer
            self.sock.settimeout(IDLE_TIMEOUT)
            with open(self.out_file, "wb") as f:
                while True:
                    try:
                        packet, addr = self.sock.recvfrom(6 + PACKET_SIZE)
                    except socket.timeout:
                        print(f"[R] No data for {IDLE_TIMEOUT}s, aborting transfer.")
                        break

                    # control packet?
                    if len(packet) == 4:
                        ctrl = struct.unpack("!I", packet)[0]
                        if ctrl == EOF_SEQ:
                            print("[R] <- EOF")
                            self.sock.sendto(struct.pack("!I", FIN), addr)
                            print("[R] -> FIN")
                            break
                        continue

                    recv_ck = struct.unpack("!H", packet[:2])[0]
                    seq     = struct.unpack("!I", packet[2:6])[0]
                    calc_ck = self.checksum(packet[2:])
                    if recv_ck != calc_ck:
                        print(f"[R] bad checksum {recv_ck}!={calc_ck}, drop#{seq}")
                        continue

                    payload = self.corrupt(packet[6:])
                    if seq == expected:
                        f.write(payload)
                        expected += 1
                        print(f"[R] wrote pkt#{seq}")

                    ackpkt = struct.pack("!I", expected - 1)
                    if random.random() < self.loss:
                        print("[R] (sim) ACK loss")
                        continue
                    self.sock.sendto(ackpkt, addr)
                    print(f"[R] -> ACK#{expected-1}")

            print("[R] Transfer finished. Waiting for next connection...\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port",       type=int,   default=5003)
    p.add_argument("--out_file",   default="received_tiger.jpg")
    p.add_argument("--error_rate", type=float, default=0.0)
    p.add_argument("--loss_rate",  type=float, default=0.0)
    args = p.parse_args()

    Receiver(args).serve()
