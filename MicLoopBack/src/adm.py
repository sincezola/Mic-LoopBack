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
buffers = defaultdict(list)  # armazena áudio por transmitter_id

def ouvir():
    def on_message(ws, message):
        data = message
        if isinstance(data, str):
            data = data.encode()

        if len(data) < 20:  # 4 bytes header + 16 bytes transmitter_id
            return

        header = data[:4]
        payload = data[4:]
        length = struct.unpack("!I", header)[0]

        transmitter_id = payload[:16]
        audio_payload = payload[16:]

        if audio_payload == b"__END__":
            print(f"Transmissor {transmitter_id.decode()} encerrou")
            return

        audio_data = np.frombuffer(audio_payload, dtype=DTYPE)
        buffers[transmitter_id].append(audio_data)

        # mistura todos os transmissores
        mixed = np.zeros_like(audio_data, dtype=np.int32)
        remove_ids = []
        for tid, buf in buffers.items():
            if buf:
                mixed += buf.pop(0).astype(np.int32)
            else:
                remove_ids.append(tid)
        # remove transmissores sem buffer
        for tid in remove_ids:
            del buffers[tid]

        mixed = np.clip(mixed, np.iinfo(DTYPE).min, np.iinfo(DTYPE).max)
        stream.write(mixed.astype(DTYPE))

    with sd.OutputStream(samplerate=SAMPLE_RATE,
                         channels=CHANNELS,
                         dtype=DTYPE,
                         blocksize=CHUNK) as stream:
        ws = websocket.WebSocketApp(ws_url, on_message=on_message)
        print("Registrando como ouvinte...")
        ws.on_open = lambda ws: ws.send(struct.pack("!I", len(b"__client_since")) + b"__client_since")
        ws.run_forever()

if __name__ == "__main__":
    ouvir()
