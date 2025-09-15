# MicLoopBack

MicLoopBack is a real-time audio relay system built with Python and WebSockets.  
It consists of three main components:

1. **`server.js`** – WebSocket relay server that handles multiple transmitters and listeners simultaneously over TCP.
2. **`client.py`** – Transmitter that captures audio from the microphone and sends it to the server.
3. **`adm.py`** – Listener client that receives audio streams from the server and plays them locally.

No database is required. All communication is handled via WebSocket over TCP.

---

## Features

- Real-time audio streaming.
- Supports multiple transmitters and listeners at the same time.
- No external database required.
- Precompiled executables are available in the `dist` folder.

---

## Folder Structure

```
MicLoopBack/
├─ server.js            # WebSocket relay server
├─ client.py            # Audio transmitter
├─ adm.py               # Audio listener
├─ dist/                # Compiled executables
│  ├─ client.exe
│  ├─ adm.exe
│  └─ ...
├─ venv/                # Python virtual environment
├─ requirements.txt     # Python dependencies
└─ README.md
```

---

## Setup

### 1. Install dependencies (Python)

Activate your virtual environment and install requirements:

```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the root folder with:

```
SERVER_URL=your_server_address:port
```

### 3. Run the server

```bash
node server.js
```

### 4. Run the clients

- **Transmitter (client.py)**:

```bash
python client.py
```

- **Listener (adm.py)**:

```bash
python adm.py
```

Or use the precompiled executables from the `dist/` folder:

```bash
dist/client.exe
dist/adm.exe
```

---

## Notes

- The server supports multiple transmitters and listeners at the same time.
- All messages are transmitted over WebSocket (WS/WSS) with unique transmitter IDs.
- The transmitters automatically register with the server when started.
- Audio is transmitted in 16-bit mono with 44.1kHz sample rate.
- The `dist` folder contains precompiled executables for convenience.

---

## License

This project is provided as-is, for educational and testing purposes.
