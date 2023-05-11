import socket
import sys

# Crear TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Unir el socket al puerto
server_address = ('localhost', 6000)
print('Inicializando el servidor {} en el puerto {}'.format(*server_address))
sock.bind(server_address)

# Buscando conexiones entrantes
sock.listen(1)

while True:
    # Espera para conectar
    print('Esperando conexion...')
    connection, client_address = sock.accept()
    try:
        print('conexion desde', client_address)

        # Recibir datos y reenviar
        while True:
            data = connection.recv(16)
            print('received {!r}'.format(data))
            if data:
                print('Reenviando datos al cliente')
                connection.sendall(data)
            else:
                print('Datos inexistentes desde', client_address)
                break

    finally:
        # Limpiar conexion
        connection.close()