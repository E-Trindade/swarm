import socket
import time
import threading
import queue
import sys

s_print_lock = threading.Lock()

METHOD_DISCOVER = 'DSCVR'
METHOD_PING     = 'PING'

COMMAND_NOOP    = 'NOOP'
COMMAND_ATTACK  = 'ATTACK'

global_peer_list = []

def s_print(*a, **b):
    """Thread safe print function"""
    #print('aaaa')
    with s_print_lock:
        print(*a, **b)
    sys.stdout.flush()

def send_message(sock, peer, msg_content='', method='', timeout=0):
    m = method + '|' if method != '' else ''
    payload = f'{m}{msg_content}'.encode()
    sock.sendto(payload, peer)

def listen_to_message(sock):
    try:
        b, addr = sock.recvfrom(2048)
        return b.decode('utf-8'), addr
    except Exception as e:
        #print(e)
        return None, None

def send_ping(peer):
    try:
        #s_print('[KEEPALIVE] Pinging to', peer)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1)
            send_message(s, peer, method=METHOD_PING)
            res, addr = listen_to_message(s)
            if addr is None: raise Exception()

            s_print('[KEEPALIVE]', peer, 'is alive', )
            return True
    except Exception as e:
        return False

def answer_ping(sock, addr):
    response = 'PONG'
    s_print('[LISTEN] Answering', addr , 'with', response)
    send_message(sock, addr, response)

def send_discover(peer, my_address):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(2)
        host, port = my_address
        send_message(s, peer, f'{host}|{port}', METHOD_DISCOVER)
        print('Contacting', peer)
        response, _ = listen_to_message(s)

        if response is None:
            return False, COMMAND_NOOP, []

        last_command, ips = response.split('|')
        return True, last_command, ips.split(',')

def answer_discover(sock, peer, last_command, peer_list):
    p_list = ','.join(map(lambda a: f'{a[0]}:{a[1]}', peer_list))
    payload = f'{last_command}|{p_list}'
    s_print('[LISTEN] Answering', peer, 'with', payload)
    send_message(sock, peer, payload)

def listen_thread(my_address, write_queue):
    s_print('Started listen_thread', flush=True)

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(my_address)

    global global_peer_list

    while True:
        try:
            data, addr = listen_to_message(udp_socket)
            s_print('[LISTEN] Incoming data from', addr, data)
            op, *args = data.split('|')

            if op == METHOD_PING:
                answer_ping(udp_socket, addr)

            if op == METHOD_DISCOVER:
                host, port = args
                answer_discover(udp_socket, addr, current_command, global_peer_list)
                write_queue.put((host, int(port)))

        except Exception as e:
            raise e

def boot_server(host='127.0.0.1', port=2048):

    SEEDS = [
        ('127.0.0.1', 1998),
        ('127.0.0.1', 1999),
        ('127.0.0.1', 2000)
    ]

    listenthread_read_queue = queue.Queue()

    t = threading.Thread(target=listen_thread, args=((host, port), listenthread_read_queue))
    t.setDaemon(True)
    t.start()

    global global_peer_list
    global_peer_list = []

    global current_command
    current_command = COMMAND_NOOP

    for peer in SEEDS:
        # Disable pinging to self
        if peer == (host, port): continue

        ok, last_command, discovered_peers = send_discover(peer, (host, port))

        if not ok:
            continue

        global_peer_list.append(peer)
        print(discovered_peers)
        for s in discovered_peers:
            if s == '': continue
            h, p = s.split(':')
            new_peer = (h, int(p))
            if new_peer not in global_peer_list:
                global_peer_list.append(new_peer)

        current_command = last_command

    while True:
        for peer in global_peer_list:
            is_alive = send_ping(peer)
            if not is_alive:
                global_peer_list.remove(peer)
                print('Removing', peer, 'from list')

        # Read new peers from queue
        try:
            while True:
                new_peer = listenthread_read_queue.get_nowait()
                s_print('[DISCOVERY] adding', new_peer , 'to peer list')
                global_peer_list.append(new_peer)
        except queue.Empty as e:
            pass
        print('[CURRENT_PEERS]', global_peer_list)
        time.sleep(5)

if __name__ == '__main__':
    boot_server(port=int(sys.argv[1]))
