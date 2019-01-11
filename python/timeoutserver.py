import socket
import sys
import signal
from threading import Thread
from threading import Lock

"""
Short program written to test the timeout handling of a microservice.
This script will accept connections and then do nothing.
"""

threads = []
shutdown = False
thread_lock = Lock()

def signal_handler(sig, frame):
    global shutdown
    print("\nSignal (%d) caught, exiting" % sig)
    with thread_lock: shutdown = True
    for thread in threads:
        thread[1].shutdown(socket.SHUT_RDWR)
        thread[0].join()
    sys.exit(0)

def listen(host, port):
    connectionCount = 0

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.bind((host, port))
    connection.listen(10)

    while True:
        con, address = connection.accept()
        connectionCount += 1
        print("[**] Connection established [%d] from %s:%d" % (connectionCount, *address))
        thread = Thread(target=handle_connection, args=(con, address, connectionCount))
        thread.start()
        threads.append((thread, con))

def handle_connection(connection, address, connectionNumber):
    while True:
        data = connection.recv(2048)
        if len(data) > 0:
            print("[**][%d] Received data from %s:%d:" % (connectionNumber, *address))
            print("[**][%d] -------------- BEGIN DATA --------------" % connectionNumber)
            print(str(data))
            print("[**][%d] -------------- END DATA ----------------" % connectionNumber)
        else:
            global shutdown
            if not shutdown:
                print("[!!][%d] Received nothing, terminating connection" % connectionNumber)
            else:
                print("[!!][%d] Terminating connection" % connectionNumber)
            break

    connection.close()

signal.signal(signal.SIGINT, signal_handler)
listen("0.0.0.0", 7070)
