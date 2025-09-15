import websocket
import sounddevice as sd
import numpy as np
import struct
from collections import defaultdict
import time
import threading
import os
from dotenv import load_dotenv

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL")
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

buffers = defaultdict(list)
running = True

def ensure_payload_multiple(audio_bytes: bytes, itemsize: int) -> bytes:
    extra = len(audio_bytes) % itemsize
    if extra != 0:
        audio_bytes = audio_bytes[:-extra]
    return audio_bytes

def play_audio(stream):
    global running
    itemsize = np.dtype(DTYPE).itemsize
    while running:
        if buffers:
            mixed = np.zeros(CHUNK, dtype=np.int32)
            remove_ids = []

            for tid, buf in list(buffers.items()):
                if buf:
                    data = buf.pop(0)
                    if data.dtype != DTYPE:
                        try:
                            data = data.astype(DTYPE)
                        except Exception:
                            print(f"[play_audio] failed to cast for {tid}, skipping frame")
                            continue
                    if data.size < CHUNK:
                        data = np.pad(data, (0, CHUNK - data.size))
                    elif data.size > CHUNK:
                        data = data[:CHUNK]
                    mixed += data.astype(np.int32)
                else:
                    remove_ids.append(tid)

            for tid in remove_ids:
                del buffers[tid]

            mixed = np.clip(mixed, np.iinfo(DTYPE).min, np.iinfo(DTYPE).max).astype(DTYPE)

            if (mixed.nbytes % itemsize) != 0:
                truncate_bytes = mixed.nbytes % itemsize
                new_len = mixed.nbytes - truncate_bytes
                new_count = new_len // itemsize
                mixed = mixed[:new_count]

            out = np.ascontiguousarray(mixed).copy()
            try:
                stream.write(out)
            except Exception as e:
                print("[play_audio] error writing to stream:", e)
                print("[play_audio] out.nbytes:", out.nbytes, "out.shape:", out.shape, "dtype:", out.dtype)
                time.sleep(0.01)
        else:
            time.sleep(0.01)

def on_message(ws, message):
    if isinstance(message, str):
        message = message.encode()

    if len(message) < 4 + 16:
        return

    try:
        declared_len = struct.unpack("!I", message[:4])[0]
    except Exception:
        declared_len = None

    payload = message[4:]
    transmitter_id = payload[:16]
    audio_payload = payload[16:]

    if audio_payload == b"__END__":
        try:
            tid_str = transmitter_id.decode(errors="ignore")
        except:
            tid_str = str(transmitter_id)
        print(f"Transmitter {tid_str} ended")
        if transmitter_id in buffers:
            del buffers[transmitter_id]
        return

    itemsize = np.dtype(DTYPE).itemsize
    audio_payload = ensure_payload_multiple(audio_payload, itemsize)

    if len(audio_payload) == 0:
        return

    try:
        audio_data = np.frombuffer(audio_payload, dtype=DTYPE)
    except Exception as e:
        print("[on_message] failed to create np.frombuffer:", e, "len(audio_payload)=", len(audio_payload))
        return

    if audio_data.size == 0:
        return

    buffers[transmitter_id].append(audio_data)

def on_error(ws, error):
    print("WS Error:", error)

def on_close(ws, close_status_code, close_msg):
    print(f"WS closed: {close_status_code} {close_msg}")

def on_open(ws):
    print("WS connected! Registering as listener...")
    try:
        ws.send(struct.pack("!I", len(b"__client_since")) + b"__client_since")
    except Exception as e:
        print("Error sending register message:", e)

def listen():
    global running
    ws_url = f"wss://{SERVER_URL}"

    while True:
        try:
            with sd.OutputStream(samplerate=SAMPLE_RATE,
                                 channels=CHANNELS,
                                 dtype=DTYPE,
                                 blocksize=CHUNK) as stream:
                running = True
                t = threading.Thread(target=play_audio, args=(stream,), daemon=True)
                t.start()

                ws_app = websocket.WebSocketApp(ws_url,
                                                on_message=on_message,
                                                on_error=on_error,
                                                on_close=on_close,
                                                on_open=on_open)
                ws_app.run_forever()
        except Exception as e:
            print("General error in listen():", e)
            print("Trying to reconnect in 3s...")
            time.sleep(3)
            buffers.clear()
        finally:
            running = False
            time.sleep(0.2)

if __name__ == "__main__":
    listen()
