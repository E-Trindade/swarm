import socket
import time
import datetime
import threading
import queue
import sys
import random

METHOD_DISCOVER      = 'DSCVR'
METHOD_PING          = 'PING'
METHOD_INIT_REPORT   = 'INIT_REPORT'
METHOD_REPORT        = 'REPORT'

COMMAND_NOOP         = 'NOOP'
COMMAND_ATTACK       = 'ATTACK'

def get_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if('127.' in ip):#then get the real local ip
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80)) #assuming no proxy
            return s.getsockname()[0] #192.168.x.x
    return ip

INIT_SEEDS = [
        (get_ip(), 1998),
        (get_ip(), 1999),
        (get_ip(), 2000),
        ('192.168.0.21', 2000)
    ]


global_peer_list = []
global_answered_reports = dict()

s_print_lock = threading.Lock()
def s_print(*a, **b):
    """Thread safe print function"""
    with s_print_lock:
        print(*a, **b)
    sys.stdout.flush()

def get_peerlist_as_string():
    global global_peer_list
    l = [host + ':' + str(port) for host, port in global_peer_list]
    return ','.join(l)

def send_message(sock, peer, msg_content='', method='', timeout=0):
    m = method + '|' if method != '' else ''
    payload = f'{m}{msg_content}'.encode()
    sock.sendto(payload, peer)

def listen_to_message(sock):
    try:
        b, addr = sock.recvfrom(2048)
        return b.decode('utf-8'), addr
    except Exception as e:
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
    payload = f'{last_command}|{get_peerlist_as_string()}'
    s_print('[LISTEN] Answering', peer, 'with', payload)
    send_message(sock, peer, payload)

def send_init_report_listener(addr):
    report_id = str(random.randint(10000, 99999))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        send_message(sock, addr, report_id, METHOD_INIT_REPORT)
        response, _ = listen_to_message(sock)
        return response

def answer_init_report_listener(callback_socket, callback_addr, my_address, report_id):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(5)
        sock.bind(('', 9999))
        for peer in global_peer_list:
            s_print('[REPORT] initial repassing REPORT to ', peer)
            send_message(sock,
                         peer,
                         my_address[0] + '|' + str(9999) + '|' + report_id,
                         METHOD_REPORT)

        received = []
        try:
            while True:
                res, addr = listen_to_message(sock)
                if addr is None:
                    raise Exception()
                received.append(res)
        except Exception as e:
            print(e)
            send_message(callback_socket, callback_addr, ' '.join(received))

def answer_report(report_to, report_id, my_address):
    global global_peer_list
    global global_answered_reports

    now = time.time()
    if report_id in global_answered_reports:
        if now - global_answered_reports[report_id] < 120: # Registry newer than 120 seconds
            print('returning')
            return
    global_answered_reports[report_id] = now

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # Return my peer list to the reporter
        s_print('[REPORT] Sending peer list to', report_to)
        send_message(sock, report_to, f'{my_address[0]}|{my_address[1]}|{get_peerlist_as_string()}')

        for peer in global_peer_list:
            s_print('[REPORT] repassing REPORT to ', peer)
            send_message(sock,
                         peer,
                         report_to[0] + '|' + str(report_to[1]) + '|' + report_id,
                         METHOD_REPORT)

def listen_thread(my_address, write_queue):
    s_print('Started listen_thread', flush=True)

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    host, port = my_address
    udp_socket.bind(('', port))

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

            if op == METHOD_INIT_REPORT:
                answer_init_report_listener(udp_socket, addr, my_address, args[0])

            if op == METHOD_REPORT:
                host, port, report_id = args
                answer_report((host, int(port)), report_id, my_address)

        except Exception as e:
            raise e

def boot_server(host='', port=2000):

    SEEDS = INIT_SEEDS

    listenthread_read_queue = queue.Queue()

    host = '192.168.1.129'
    t = threading.Thread(target=listen_thread, args=((host, port), listenthread_read_queue))
    t.setDaemon(True)
    t.start()

    global global_peer_list
    global_peer_list = []

    global current_command
    current_command = COMMAND_NOOP

    verify_seeds(SEEDS,global_peer_list,current_command,host, port)

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
        if not global_peer_list:
            time.sleep(5)
            print("re-initialize")
            verify_seeds(SEEDS,global_peer_list,current_command,host, port)

def verify_seeds(SEEDS,global_peer_list,current_command,host, port):
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

if __name__ == '__main__':
    port=int(sys.argv[1])
    ip = get_ip()
    print('Initialize hosname: ', socket.gethostname(),' at address:',ip,':',port,'on:',datetime.datetime.now())
    boot_server(ip,port)
