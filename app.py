from flask import Flask, jsonify, render_template
import os
import socket
import json
from ping3 import ping

app = Flask(__name__)

# 🔹 Load configuration from JSON file
with open('config.json', 'r') as config_file:
    cfg = json.load(config_file)

# 🔹 Function to send a Wake-on-LAN Magic Packet
def send_wol(mac_address):
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    magic_packet = b'\xff' * 6 + mac_bytes * 16

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic_packet, ('<broadcast>', 9))

# 🔹 Function to check if Windows PC is online
def is_pc_online():
    response = ping(cfg['TARGET_IP'], timeout=1)
    return response is not None

@app.route("/")
def home():
    status = "Online" if is_pc_online() else "Offline"
    return render_template("index.html", status=status)

@app.route("/wake", methods=["POST"])
def wake():
    send_wol(cfg['TARGET_MAC'])
    return jsonify({"message": "Magic Packet Sent!"})

@app.route("/sleep", methods=["POST"])
def sleep():
    os.system(f"ssh -i {cfg['SSH_KEY_PATH']} {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"rundll32.exe powrprof.dll,SetSuspendState 0,1,0\"")
    return jsonify({"message": "PC is now sleeping!"})

@app.route("/hibernate", methods=["POST"])
def hibernate():
    os.system(f"ssh -i {cfg['SSH_KEY_PATH']} {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"shutdown /h\"")
    return jsonify({"message": "PC is now hibernating!"})

@app.route("/shutdown", methods=["POST"])
def shutdown():
    os.system(f"ssh -i {cfg['SSH_KEY_PATH']} {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"shutdown /s /t 0\"")
    return jsonify({"message": "PC is shutting down!"})

@app.route("/restart", methods=["POST"])
def restart():
    os.system(f"ssh -i {cfg['SSH_KEY_PATH']} {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"shutdown /r /t 0\"")
    return jsonify({"message": "PC is restarting!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg['PORT'], debug=cfg['DEBUG'])