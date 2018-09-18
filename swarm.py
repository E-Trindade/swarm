import socket
import time
import threading
import queue
import sys
s_print_lock = threading.Lock()

def s_print(*a, **b):
    """Thread safe print function"""
    with s_print_lock:
        print(*a, **b)
def listen_socket(udp_socket, up_queue, down_queue):
    sprint('aaaa')
    while True:
        data, addr = sock.recvfrom(1024)
        data = data.decode('utf-8')
        op, *args, hash = data.split('|')

        print(op, args, hash)

        if op == 'PING':
            print('PONG')
            sock.sendto(b'PONG\n', addr)

        if op == 'DSCVR':
            sock.sendto(b'||127.0.0.1', addr)

def boot_server(host='127.0.0.1', port=2048):
    MESSAGE = "Hello, World!"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    up_queue = queue.Queue()
    down_queue = queue.Queue()

    t = threading.Thread(target=listen_socket, args=(sock, up_queue, down_queue))
    while True:
        print(1)
        time.sleep(1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b'PING|',('127.0.0.1', 2048))

if __name__ == '__main__':
    boot_server(port=int(sys.argv[1]))
