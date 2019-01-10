import socket
from threading import Thread

"""
Short program written to test the timeout handling of a microservice.
This script will accept a connection and then do nothing.
"""

def listen(host, port):
    threads = []
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
        threads.append(thread)

def handle_connection(connection, address, connectionNumber):
    while True:
        data = connection.recv(2048)
        if len(data) > 0:
            print("[**][%d] Received data from %s:%d:" % (connectionNumber, *address))
            print("[**][%d] -------------- BEGIN DATA --------------" % connectionNumber)
            print(str(data))
            print("[**][%d] -------------- END DATA ----------------" % connectionNumber)
        else:
            print("[!!][%d] Received nothing, terminating client" % connectionNumber)
            break

    connection.close()

listen("0.0.0.0", 7070)
