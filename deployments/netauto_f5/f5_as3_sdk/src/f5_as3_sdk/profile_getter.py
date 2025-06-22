import requests, warnings, json, base64, os, pathlib, sys, copy

F5 = "10.17.90.12"
# options are tcp, http, client-ssl, server-ssl
PROFILES = "tcp"
USERNAME = "admin"
PASSWORD = "1234Qwer"


warnings.filterwarnings("ignore")
b64_string = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode("ascii")).decode("ascii")
headers = {"Content-Type":"application/json", "Authorization": f"Basic {b64_string}"}

tcp_defaults = ["apm-forwarding-client-tcp","apm-forwarding-server-tcp","f5-tcp-lan","f5-tcp-mobile","f5-tcp-wan","mptcp-mobile-optimized","splitsession-default-tcp","tcp","tcp-lan-optimized","tcp-legacy","tcp-mobile-optimized","tcp-wan-optimized","wom-tcp-lan-optimized","wom-tcp-wan-optimized", "f5-tcp-progressive"]
http_defaults = ["http","http-explicit","http-transparent"]
client_ssl_defaults = ["clientssl","clientssl-insecure-compatible","clientssl-quic","clientssl-secure","crypto-server-default-clientssl","splitsession-default-clientssl","wom-default-clientssl"]
server_ssl_defaults = ["apm-default-serverssl","cloud-service-default-ssl","crypto-client-default-serverssl","do-not-remove-without-replacement","f5aas-default-ssl","pcoip-default-serverssl","serverssl","serverssl-insecure-compatible","serverssl-secure","shape-api-ssl","splitsession-default-serverssl","wom-default-serverssl"]

r = requests.get(f"https://{F5}/mgmt/tm/ltm/profile/{PROFILES}", headers=headers, verify=False)
data = r.json()

defaults_all = copy.deepcopy(tcp_defaults)
defaults_all.extend(http_defaults)
defaults_all.extend(client_ssl_defaults)
defaults_all.extend(server_ssl_defaults)

profiles = []
for it in data.get("items"):
   if it.get("name") not in defaults_all:
      profiles.append(it["name"])

print(profiles)