import socket
import sys
import signal
import termstyle as sty
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
    print("")
    fatal("Signal (%d) caught, shutting down" % sig)
    with thread_lock: shutdown = True
    log("Shutting down %d connection(s)" % len(threads))
    for thread in threads:
        thread[1].shutdown(socket.SHUT_RDWR)
        thread[0].join()
    sys.exit(0)

def log(msg, inst=0):
    if inst > 0:
        instance = "[%d]" % inst
    else:
        instance = ""
    print("%s[**]%s%s %s%s" % (sty.yellow, instance, sty.green, msg, sty.reset))

def error(msg, inst=0):
    if inst > 0:
        instance = "[%d]" % inst
    else:
        instance = ""
    print("%s[!!]%s%s %s%s" % (sty.yellow, instance, sty.green, msg, sty.reset))

def fatal(msg, inst=0):
    if inst > 0:
        instance = "[%d]" % inst
    else:
        instance = ""
    print("%s[!!]%s%s %s%s" % (sty.red, instance, sty.yellow, msg, sty.reset))

def listen(host, port):
    connectionCount = 0

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    log("Listening on %s:%d" % (host, port))
    connection.bind((host, port))
    connection.listen(10)

    while True:
        con, address = connection.accept()
        connectionCount += 1
        log("Connection established from %s:%d" % address, connectionCount)
        thread = Thread(target=handle_connection, args=(con, address, connectionCount))
        thread.start()
        threads.append((thread, con))

def handle_connection(connection, address, connectionNumber):
    while True:
        data = connection.recv(2048)
        if len(data) > 0:
            log("Received data from %s:%d:" % address, connectionNumber)
            log("-------------- BEGIN DATA --------------", connectionNumber)
            print(str(data))
            log("-------------- END DATA ----------------", connectionNumber)
        else:
            global shutdown
            if not shutdown:
                error("Received nothing, terminating connection", connectionNumber)
            else:
                error("Terminating connection", connectionNumber)
            break

    connection.close()

signal.signal(signal.SIGINT, signal_handler)
listen("0.0.0.0", 7070)
