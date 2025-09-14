# client_tx.py
import socket
import sounddevice as sd
import numpy as np
import struct

SERVER_IP = "127.0.0.1"
PORT = 5000
SAMPLE_RATE = 44100
CHUNK = 1024
CHANNELS = 1
DTYPE = np.int16

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, PORT))
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

def send_frame(data_bytes: bytes):
    header = struct.pack("!I", len(data_bytes))  # 4 bytes big-endian
    sock.sendall(header + data_bytes)

def callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    # indata é array shape (CHUNK, CHANNELS), dtype float by default or provided dtype
    # estamos assumindo dtype np.int16 in stream configuration
    send_frame(indata.tobytes())

# se quiser, force dtype=np.int16 in InputStream (compatível com seu server)
with sd.InputStream(samplerate=SAMPLE_RATE, blocksize=CHUNK,
                    channels=CHANNELS, dtype=DTYPE,
                    callback=callback):
    print("Capturando áudio e enviando para", SERVER_IP, PORT)
    try:
        input("Pressione Enter para parar...\n")
    except KeyboardInterrupt:
        pass

# sinaliza fim
send_frame(b"__END__")
sock.close()
