from termux_desk import TermuxDeskServer

server = TermuxDeskServer(host="127.0.0.1", port=8765)
print(f"Open {server.local_url}")
server.run()
