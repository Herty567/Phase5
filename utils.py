# utils.py

def compute_checksum(data: bytes) -> int:
    """
    16-bit Internet checksum over `data`, same as in both
    sender.py and receiver.py but defined exactly once.
    """
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + (data[i+1] if i+1 < len(data) else 0)
        s = (s + w) & 0xFFFF
    return s
