import websocket
import sounddevice as sd
import numpy as np
import struct
from collections import defaultdict

SERVER_URL = "mic-loopback.onrender.com"
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

ws_url = f"ws://{SERVER_URL}"
buffers = defaultdict(list)

def ouvir():
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
            return

        audio_data = np.frombuffer(audio_payload, dtype=DTYPE)
        buffers[transmitter_id].append(audio_data)

        # mistura todos os transmissores, garantindo tamanho CHUNK
        mixed = np.zeros(CHUNK, dtype=np.int32)
        remove_ids = []
        for tid, buf in buffers.items():
            if buf:
                # ajusta tamanho se necessário
                data = buf.pop(0)
                if len(data) < CHUNK:
                    data = np.pad(data, (0, CHUNK - len(data)))
                elif len(data) > CHUNK:
                    data = data[:CHUNK]
                mixed += data.astype(np.int32)
            else:
                remove_ids.append(tid)
        for tid in remove_ids:
            del buffers[tid]

        mixed = np.clip(mixed, np.iinfo(DTYPE).min, np.iinfo(DTYPE).max)
        stream.write(mixed.astype(DTYPE))

    def on_error(ws, error):
        print("WS Error:", error)

    def on_close(ws, close_status_code, close_msg):
        print(f"WS closed: {close_status_code} {close_msg}")

    def on_open(ws):
        print("WS conectado! Registrando como ouvinte...")
        ws.send(struct.pack("!I", len(b"__client_since")) + b"__client_since")

    with sd.OutputStream(samplerate=SAMPLE_RATE,
                         channels=CHANNELS,
                         dtype=DTYPE,
                         blocksize=CHUNK) as stream:
        ws = websocket.WebSocketApp(ws_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    on_open=on_open)
        ws.run_forever()

if __name__ == "__main__":
    ouvir()
