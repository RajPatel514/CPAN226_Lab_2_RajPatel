# This program was modified by Raj Patel / n01715368

import socket
import argparse
import os
import struct
DEBUG = False 

def run_client(target_ip, target_port, input_file):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (target_ip, target_port)
    sock.settimeout(0.3)  # 300ms timeout for ACKs

    if not os.path.exists(input_file):
        print(f"[!] Error: File '{input_file}' not found.")
        return

    try:
        with open(input_file, 'rb') as f:
            file_data = f.read()

        chunk_size = 1450
        chunks = [file_data[i:i + chunk_size] for i in range(0, len(file_data), chunk_size)]

        seq_num = 0
        total_chunks = len(chunks)
        MAX_RETRIES = 50

        while seq_num < total_chunks:
            header = struct.pack('!I', seq_num)
            packet = header + chunks[seq_num]

            if DEBUG:
                print(f"[*] Sending seq {seq_num} ({len(chunks[seq_num])} bytes)")

            retries = 0
            while True:
                sock.sendto(packet, server_address)

                try:
                    ack_data, _ = sock.recvfrom(1024)
                    if len(ack_data) != 4:
                        continue

                    ack_seq = struct.unpack('!I', ack_data)[0]

                    if ack_seq == seq_num:
                        if DEBUG:
                            print(f"[+] ACK {ack_seq}")
                        seq_num += 1
                        break  
                    else:
                        continue
                except socket.timeout:
                    retries += 1
                    if retries >= MAX_RETRIES:
                        print(f"[!] Too many timeouts on seq {seq_num}. Aborting.")
                        return
            if seq_num % 25 == 0 or seq_num == total_chunks:
                print(f"[*] Progress: {seq_num}/{total_chunks} packets ACKed")
        eof_seq = 0xFFFFFFFF
        eof_packet = struct.pack('!I', eof_seq)
        retries = 0
        while True:
            sock.sendto(eof_packet, server_address)
            try:
                ack_data, _ = sock.recvfrom(1024)
                if len(ack_data) != 4:
                    continue

                ack_seq = struct.unpack('!I', ack_data)[0]
                if ack_seq == eof_seq:
                    print("[*] EOF ACK received. File transmission complete.")
                    break

            except socket.timeout:
                retries += 1
                if retries >= MAX_RETRIES:
                    print("[!] Too many timeouts waiting for EOF ACK. Aborting.")
                    return

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP File Sender (Stop-and-Wait + Seq)")
    parser.add_argument("--target_ip", type=str, default="127.0.0.1", help="Destination IP (Relay or Server)")
    parser.add_argument("--target_port", type=int, default=12000, help="Destination Port")
    parser.add_argument("--file", type=str, required=True, help="Path to file to send")
    args = parser.parse_args()
    run_client(args.target_ip, args.target_port, args.file)
