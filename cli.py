#!/usr/bin/env python

import sys
import argparse
import getpass

from swarm import METHOD_REPORT
from swarm import send_ping, send_init_report_listener

INPUT_REPORT = 'report'
INPUT_ATTACK = 'attack'
INPUT_EXIT   = 'exit'

def do_report(addr, to_print=True):
    report = send_init_report_listener(addr)
    report = report.replace(' ', '\n')
    lines = report.split('\n')
    if not to_print: return lines
    for line in lines:
        ip, port, peers = line.split('|')
        print(f'{ip}:{port} ->')
        for peer in peers.split(','):
            print(f'\t{peer}')
    return lines

def do_report_graphic(addr):
    from graphviz import Graph
    lines = do_report(addr)
    graph = Graph()
    for line in lines:
        host, port, peers_s = line.split('|')
        src = f'{host}:{port}'
        for dst in peers_s.split(','):
            graph.edge(src, dst)
    return graph



def do_attack(addr):
    pass

def main(args):
    print(f'''Hello there.
You are connected to: {args.host}:{args.port}
Available commands:

report               - Get overview of network
attack <host> <port> - Instruct network to attack target
exit                 - Close this awesome tool
    ''')

    addr = (args.host, args.port)
    if not send_ping(addr):
        print('Error: host could not be contacted')
        return

    while True:
        try:
            t = input(f'swarm@{args.host}:{args.port} > ')
            if t == INPUT_REPORT:
                do_report(addr)

            if t == INPUT_EXIT:
                break

            cmd, host, port = t.split()
            if cmd == INPUT_ATTACK:
                do_attack(addr)

        except ValueError:
            pass

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description = 'Does a thing to some stuff.',
      add_help = True
  )

  parser.add_argument(
      'host',
      help = 'host to connect',
      default= '127.0.0.1',
      metavar = 'host')

  parser.add_argument(
      'port',
      help = "host's port to use",
      type = int,
      metavar = 'port')

  args = parser.parse_args()
  main(args)
