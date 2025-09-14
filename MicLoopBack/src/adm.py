import websocket
import sounddevice as sd
import numpy as np
import struct

SERVER_URL = "mic-loopback.onrender.com"
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

ws_url = f"ws://{SERVER_URL}"

def ouvir():
    def on_message(ws, message):
        data = message
        if isinstance(data, str):
            data = data.encode()

        if len(data) < 4:
            return

        header = data[:4]
        payload = data[4:]
        length = struct.unpack("!I", header)[0]

        if payload == b"__END__":
            print("Recebido __END__")
            ws.close()
            return

        audio_data = np.frombuffer(payload, dtype=DTYPE)
        stream.write(audio_data)

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
