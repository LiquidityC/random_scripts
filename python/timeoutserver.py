import socket

"""
Short program written to test the timeout handling of a microservice.
This script will accept a connection and then do nothing.
"""

def listen(host, port):
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.bind((host, port))
    connection.listen(10)
    while True:
        cur_connection, address = connection.accept()
        print("[**] Connection established from %s:%d" % address)

        while True:
            data = cur_connection.recv(2048)
            if len(data) > 0:
                print("[**] Received data from %s:%d:" % address)
                print("[**] -------------- BEGIN DATA --------------")
                print(str(data))
                print("[**] -------------- END DATA ----------------")
            else:
                print("[!!] Received nothing, terminating client")
                break

        cur_connection.close()

listen("0.0.0.0", 7070)
