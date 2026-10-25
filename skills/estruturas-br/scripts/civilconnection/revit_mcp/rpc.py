# Minimal JSON-RPC client for the mcp-servers-for-revit socket (127.0.0.1:8080).
# Requests and responses are newline-delimited JSON.
import json, socket, sys, uuid


def call(method, params, timeout=300):
    req = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": str(uuid.uuid4())}) + "\n"
    with socket.create_connection(("127.0.0.1", 8080), timeout=timeout) as s:
        s.sendall(req.encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.decode("utf-8"))


if __name__ == "__main__":
    method = sys.argv[1]
    params = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else {}
    print(json.dumps(call(method, params), indent=1, ensure_ascii=False)[:8000])
