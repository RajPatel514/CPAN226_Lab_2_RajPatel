# This program was modified by Raj Patel / n01715368
import socket
import argparse
import struct
from collections import OrderedDict
DEBUG = False

def run_server(port, output_file):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('', port)
    sock.bind(server_address)

    expected_seq_num = 0
    buffer = OrderedDict()
    received_data = bytearray()

    try:
        while True:
            data, addr = sock.recvfrom(4096 + 4)

            if not data:
                continue
            if len(data) < 4:
                continue

            seq_num = struct.unpack('!I', data[:4])[0]
            packet_data = data[4:]

            
            if seq_num == 0xFFFFFFFF:
                print(f"[*] EOF received from {addr}")

                if received_data:
                    with open(output_file, 'wb') as f:
                        f.write(received_data)
                    print(f"[*] File saved '{output_file}'")
                sock.sendto(struct.pack('!I', seq_num), addr)
                expected_seq_num = 0
                buffer.clear()
                received_data = bytearray()
                continue
            sock.sendto(struct.pack('!I', seq_num), addr)

            if seq_num == expected_seq_num:
                received_data.extend(packet_data)
                expected_seq_num += 1

                while expected_seq_num in buffer:
                    if DEBUG:
                        print(f"[*] Flushing buffered seq {expected_seq_num}")
                    received_data.extend(buffer.pop(expected_seq_num))
                    expected_seq_num += 1

            elif seq_num > expected_seq_num:
                if seq_num not in buffer:
                    buffer[seq_num] = packet_data
                    if DEBUG:
                        print(f"[*] Stored out-of-order {seq_num}")

            else:
                if DEBUG:
                    print(f"[*] Duplicate {seq_num} ignored")

    except KeyboardInterrupt:
        print("\n[!] Server stopped.")
        if received_data:
            with open(output_file, 'wb') as f:
                f.write(received_data)
            print(f"[*] Incomplete file '{output_file}'")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        sock.close()
        print("[*] Server closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP File Receiver (Buffer + ACK)")
    parser.add_argument("--port", type=int, default=12001, help="Port to listen on")
    parser.add_argument("--output", type=str, default="received_file.jpg", help="File path to save data")
    args = parser.parse_args()

    run_server(args.port, args.output)
