from flask import Flask, jsonify, render_template, request
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

# 🔹 Function to check if client MAC is allowed
def is_mac_allowed(client_ip):
    # Get MAC address from IP using ARP table
    try:
        # For Linux/Unix systems
        import subprocess
        output = subprocess.check_output(f"arp -n {client_ip}", shell=True).decode('utf-8')
        mac_lines = [line for line in output.split('\n') if client_ip in line]
        if mac_lines:
            parts = mac_lines[0].split()
            if len(parts) >= 3:
                client_mac = parts[3].lower() 
                print(f"Client MAC: {client_mac}")
                is_allowed =client_mac in [mac.lower() for mac in cfg['ALLOWED_MACS']]
                if not is_allowed:
                    print(f"Access denied for {client_mac}")
                return is_allowed
    except Exception as e:
        print(f"Error getting MAC address: {e}")
    return False

# 🔹 Decorator to check MAC address before processing requests
def check_mac_access(func):
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        if not is_mac_allowed(client_ip):
            return jsonify({"error": "Access denied. Your device is not authorized."}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/")
@check_mac_access
def home():
    status = "Online" if is_pc_online() else "Offline"
    return render_template("index.html", status=status)

@app.route("/wake", methods=["POST"])
@check_mac_access
def wake():
    send_wol(cfg['TARGET_MAC'])
    return jsonify({"message": "Magic Packet Sent!"})

@app.route("/sleep", methods=["POST"])
@check_mac_access
def sleep():
    os.system(f"ssh {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"rundll32.exe powrprof.dll,SetSuspendState 0,1,0\"")
    return jsonify({"message": "PC is now sleeping!"})

@app.route("/hibernate", methods=["POST"])
@check_mac_access
def hibernate():
    os.system(f"ssh {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"shutdown /h\"")
    return jsonify({"message": "PC is now hibernating!"})

@app.route("/shutdown", methods=["POST"])
@check_mac_access
def shutdown():
    os.system(f"ssh {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"shutdown /s /t 0\"")
    return jsonify({"message": "PC is shutting down!"})

@app.route("/restart", methods=["POST"])
@check_mac_access
def restart():
    os.system(f"ssh {cfg['SSH_USER']}@{cfg['SSH_HOST']} powershell.exe -Command \"shutdown /r /t 0\"")
    return jsonify({"message": "PC is restarting!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg['PORT'], debug=cfg['DEBUG'])