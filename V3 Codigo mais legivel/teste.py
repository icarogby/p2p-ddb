import socket

# Obtém o nome do host da máquina local
host_name = socket.gethostname()

# Obtém todas as informações de endereço associadas ao nome do host
info = socket.getaddrinfo(host_name, None, socket.AF_INET6)[2][4][0]

# Filtra as informações para obter o endereço IPv6
#ipv6_address = next(addr[4][0] for addr in info if addr[1] == socket.SOCK_STREAM and addr[0] == socket.AF_INET6)

print(f"Endereço IPv6 da máquina local: {info}")