import { WebSocketServer } from "ws";
import { config } from "dotenv";
import { randomUUID } from "crypto";

config();

const PORT = process.env.PORT || 5000;

const wss = new WebSocketServer({ port: PORT });
const clients = new Set();

function makeKey(ws) {
  return ws._id || "unknown";
}

wss.on("connection", (ws, req) => {
  ws._buffer = Buffer.alloc(0);
  ws._registered = false;
  ws._type = null;
  ws._id = randomUUID();
  clients.add(ws);

  console.log("Cliente conectado:", makeKey(ws));

  ws.on("message", (data) => {
    const chunk = Buffer.isBuffer(data) ? data : Buffer.from(data);
    ws._buffer = Buffer.concat([ws._buffer, chunk]);

    while (ws._buffer.length >= 4) {
      const len = ws._buffer.readUInt32BE(0);
      if (ws._buffer.length < 4 + len) break;

      const payload = ws._buffer.slice(4, 4 + len);
      ws._buffer = ws._buffer.slice(4 + len);

      if (payload.toString() === "__client_since") {
        ws._type = "listener";
        ws._registered = true;
        console.log("Ouvinte registrado:", makeKey(ws));
        continue;
      }

      if (!ws._registered) {
        ws._id = payload.slice(0, 16).toString();
        ws._type = "transmitter";
        ws._registered = true;
      }

      if (payload.slice(16).toString() === "__END__") {
        console.log("Transmissor encerrou:", makeKey(ws));
        continue;
      }

      for (const client of clients) {
        if (client === ws) continue;
        if (client._type !== "listener" || !client._registered) continue;

        try {
          const header = Buffer.alloc(4);
          header.writeUInt32BE(payload.length, 0);
          client.send(Buffer.concat([header, payload]));
        } catch (err) {
          console.error("Erro ao enviar para", makeKey(client), err);
        }
      }
    }
  });

  ws.on("close", () => {
    clients.delete(ws);
    console.log("Cliente desconectado:", makeKey(ws));
  });

  ws.on("error", (err) => {
    clients.delete(ws);
    console.error("Erro WS", makeKey(ws), err);
  });
});

console.log(`Relay WebSocket ouvindo na porta ${PORT}`);
