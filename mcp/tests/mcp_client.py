"""Minimal MCP stdio client used to test the Civil Senior servers (newline-delimited JSON-RPC)."""
import json
import subprocess
import sys


class McpClient:
    def __init__(self, command):
        self.p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, encoding="utf-8", bufsize=1)
        self.next_id = 0
        init = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "civil-senior-test", "version": "1.0"}})
        self.server = init["result"]["serverInfo"]
        self.notify("notifications/initialized", {})

    def notify(self, method, params):
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.p.stdin.flush()

    def request(self, method, params):
        self.next_id += 1
        rid = self.next_id
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("server closed the connection")
            msg = json.loads(line)
            if msg.get("id") == rid:
                return msg

    def tools(self):
        return self.request("tools/list", {})["result"]["tools"]

    def call(self, _tool, **arguments):
        msg = self.request("tools/call", {"name": _tool, "arguments": arguments})
        if "error" in msg:
            raise RuntimeError(f"{_tool}: {msg['error']}")
        text = msg["result"]["content"][0]["text"]
        data = json.loads(text)
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"{_tool}: {data['error']}")
        return data

    def close(self):
        self.p.stdin.close()
        self.p.wait(10)


if __name__ == "__main__":
    c = McpClient(sys.argv[1:])
    print(c.server)
    for t in c.tools():
        print("-", t["name"])
    c.close()
