import socket
import time
import threading
import queue
import sys
s_print_lock = threading.Lock()

def s_print(*a, **b):
    """Thread safe print function"""
    #print('aaaa')
    with s_print_lock:
        print(*a, **b)
    sys.stdout.flush()

def listen_thread(udp_socket, read_queue, write_queue):
    s_print('Started listen_thread', flush=True)
    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)
            s_print('[LISTEN] Incoming data from', addr, data)
            data = data.decode('utf-8')
            op, *args = data.split('|')

            if op == 'PING':
                response = b'PONG\n'
                s_print('[LISTEN] Answering', addr , 'with', response)
                udp_socket.sendto(response, addr)

            if op == 'DSCVR':
                response = b'||127.0.0.1'
                s_print('[LISTEN] Answering', addr , 'with', response)
                write_queue.put((args[0], int(args[1])))
                udp_socket.sendto(response, addr)
        except Exception as e:
            print(e)

def boot_server(host='127.0.0.1', port=2048):

    SEEDS = [
        ('127.0.0.1', 1998),
        ('127.0.0.1', 1999),
        ('127.0.0.1', 2000)
    ]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    listenthread_read_queue = queue.Queue()
    listenthread_write_queue = queue.Queue()

    t = threading.Thread(target=listen_thread, args=(sock, listenthread_write_queue, listenthread_read_queue))
    t.setDaemon(True)
    t.start()

    peers = []

    for peer in SEEDS:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(f'DSCVR|{host}|{port}'.encode(), peer)
        print('Contacting', peer)
        peers.append(peer)

    while True:
        for peer in peers:
            try:
                s_print('[KEEPALIVE] Pinging to', peer)

                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1)
                s.sendto(b'PING|\n', peer)
                s.recv(1024)
                s_print('[KEEPALIVE]', peer, 'is alive', )

            except Exception as e:
                #print('Failed', e)
                #TODO remove peer from list
                #print(e)
                pass

            # Get peers
            try:
                new_peer = listenthread_read_queue.get_nowait()
                s_print('[DISCOVERY] adding', new_peer , 'to peer list')
                peers.append(new_peer)
            except queue.Empty as e:
                pass

        time.sleep(5)

if __name__ == '__main__':
    boot_server(port=int(sys.argv[1]))
