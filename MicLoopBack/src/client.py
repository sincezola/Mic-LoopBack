import websocket
import sounddevice as sd
import numpy as np
import struct

SERVER_IP = "127.0.0.1"
PORT = 5000
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

ws_url = f"ws://{SERVER_IP}:{PORT}"
ws = websocket.WebSocket()
ws.connect(ws_url)

def send_frame(data_bytes: bytes):
    header = struct.pack("!I", len(data_bytes))
    ws.send(header + data_bytes, opcode=websocket.ABNF.OPCODE_BINARY)

def callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    send_frame(indata.tobytes())

with sd.InputStream(samplerate=SAMPLE_RATE,
                    blocksize=CHUNK,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    callback=callback):
    print("Capturando áudio e enviando...")
    try:
        input("Pressione Enter para parar...\n")
    except KeyboardInterrupt:
        pass

send_frame(b"__END__")
ws.close()
