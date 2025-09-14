import websocket
import sounddevice as sd
import numpy as np
import struct
from collections import defaultdict
import time
import threading

SERVER_URL = "mic-loopback.onrender.com"
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

buffers = defaultdict(list)
running = True  # controla o loop de áudio

# --- Callback para misturar e tocar áudio ---
def play_audio(stream):
    global running
    while running:
        if buffers:
            # mistura todos os transmissores
            mixed = np.zeros(CHUNK, dtype=np.int32)
            remove_ids = []

            for tid, buf in buffers.items():
                if buf:
                    data = buf.pop(0)
                    # garante tamanho CHUNK
                    if len(data) < CHUNK:
                        data = np.pad(data, (0, CHUNK - len(data)))
                    elif len(data) > CHUNK:
                        data = data[:CHUNK]
                    mixed += data.astype(np.int32)
                else:
                    remove_ids.append(tid)

            for tid in remove_ids:
                del buffers[tid]

            # converte para int16 e garante múltiplo do elemento
            mixed = np.clip(mixed, np.iinfo(DTYPE).min, np.iinfo(DTYPE).max).astype(DTYPE)
            stream.write(mixed)
        else:
            # nenhum transmissor ativo, espera um pouco
            time.sleep(0.01)

# --- Funções de WebSocket ---
def on_message(ws, message):
    if isinstance(message, str):
        message = message.encode()

    if len(message) < 20:
        return

    length = struct.unpack("!I", message[:4])[0]
    payload = message[4:]

    transmitter_id = payload[:16]
    audio_payload = payload[16:]

    if audio_payload == b"__END__":
        print(f"Transmissor {transmitter_id.decode()} encerrou")
        if transmitter_id in buffers:
            del buffers[transmitter_id]
        return

    audio_data = np.frombuffer(audio_payload, dtype=DTYPE)
    buffers[transmitter_id].append(audio_data)

def on_error(ws, error):
    print("WS Error:", error)

def on_close(ws, close_status_code, close_msg):
    print(f"WS closed: {close_status_code} {close_msg}")

def on_open(ws):
    print("WS conectado! Registrando como ouvinte...")
    ws.send(struct.pack("!I", len(b"__client_since")) + b"__client_since")

# --- Função principal ---
def ouvir():
    global running
    ws_url = f"wss://{SERVER_URL}"

    while True:
        try:
            with sd.OutputStream(samplerate=SAMPLE_RATE,
                                 channels=CHANNELS,
                                 dtype=DTYPE,
                                 blocksize=CHUNK) as stream:
                # Thread separada para tocar áudio
                t = threading.Thread(target=play_audio, args=(stream,), daemon=True)
                t.start()

                ws_app = websocket.WebSocketApp(ws_url,
                                                on_message=on_message,
                                                on_error=on_error,
                                                on_close=on_close,
                                                on_open=on_open)
                ws_app.run_forever()
        except Exception as e:
            print("Erro geral:", e)
            print("Tentando reconectar em 3 segundos...")
            time.sleep(3)
        finally:
            running = True  # garante que a thread de áudio continue

if __name__ == "__main__":
    ouvir()
