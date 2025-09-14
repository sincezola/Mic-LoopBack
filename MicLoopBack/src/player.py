# client_rx.py
import socket
import sounddevice as sd
import numpy as np
import struct

SERVER_IP = "127.0.0.1"
PORT = 5000
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
DTYPE = np.int16

def recvall(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, PORT))
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

# registra como ouvinte
hdr = struct.pack("!I", len(b"__client_since"))
sock.sendall(hdr + b"__client_since")
print("Registrado como ouvinte em", SERVER_IP, PORT)

def ouvir():
    with sd.OutputStream(samplerate=SAMPLE_RATE,
                         channels=CHANNELS,
                         dtype=DTYPE,
                         blocksize=CHUNK) as stream:
        print("Aguardando áudio...")
        while True:
            # recebe header
            h = recvall(sock, 4)
            if h is None:
                print("Conexão fechada pelo servidor.")
                break
            (length,) = struct.unpack("!I", h)
            payload = recvall(sock, length)
            if payload is None:
                print("Conexão fechada durante payload.")
                break

            # se payload textual __END__ possivelmente do servidor/transmissor
            if payload == b"__END__":
                print("Recebido __END__")
                break

            # payload é áudio em int16
            audio_data = np.frombuffer(payload, dtype=DTYPE)
            # pode ser necessário reshape se canais >1
            stream.write(audio_data)

if __name__ == "__main__":
    try:
        ouvir()
    except KeyboardInterrupt:
        print("\nEncerrando cliente ouvinte...")
    finally:
        sock.close()
