import socket
from threading import Thread

# endereço que o tracker vai se conectar
connect_to = None

# Endereço do tracker
host = socket.gethostbyname(socket.gethostname())
port = 2000

# lista de peers conectados
peers_list = [(socket.gethostbyname(socket.gethostname()), 2000)]

print(f"HOST: {host} PORT: {port}")

# Socket cliente
clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Socket servidor
svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
svr.bind((host, port))
svr.listen(5)

def tracker():
    global peers_list
    global connect_to
    global clt
    global svr

    while True:
        # Aceita conexão pelo lado servidor
        con, adr = svr.accept()

        while True:
            print(peers_list)

            #recebe a mensagem do ultimo par da rede ou de novo par
            data = con.recv(1024)
            commands = data.decode("utf-8")

            # Se uma conexão for fechada, sai do loop e espera uma nova conexão
            if not data:
                break
            
            # Separa e executa os comandos
            for command in commands.split("|"):
                if command == "":
                    continue

                print(f"Comando recebido pelo traker: {command}")

                # data1 = Destino | data2 = Comando | data3 = Informação personalizada
                data1, data2, data3, = command.split(";")

                # Novo peer entra na rede e pede para receber identificação
                if(data1 == "ID"):
                    peers_list.append((adr[0], int(data3)))

                    # Se for o primeiro peer da rede, tracker se conecta com ele
                    if(len(peers_list) == 2):
                        connect_to = peers_list[1]
                        clt.connect(connect_to)
                        clt.send(f"ID;NEW_ID;{len(peers_list) - 1}|".encode("utf-8"))
                    
                    # Se não for o unico par da rede, vai ser o novo ultimo par
                    if(len(peers_list) > 2):
                        old_final_peer_number = len(peers_list) - 2

                        # Comando para antigo ultimo par, conecte-se com o novo ultimo par
                        clt.send(f"P{old_final_peer_number};CONNECT_WITH;{peers_list[-1]}|".encode("utf-8"))

                        # Novo ultimo par, esse é seu id
                        clt.send(f"ID;NEW_ID;{len(peers_list) - 1}|".encode("utf-8"))

                # Mensagem para os peers       
                elif(data1[0] == "P"):
                    # Faz o pedido de novo id parar de circular
                    if data2 == "NEW_ID":
                        pass
                    # Mantem a mensagem circulando no anel
                    else:
                        clt.send(f"{command}|".encode("utf-8"))
                
                # Mensagem para o tracker
                elif(data1 == "TK"):
                    # Remove um peer da rede
                    if(data2 == "REMOVE_FROM_LIST"):
                        # Caso o peer que saiu seja o ultimo da rede
                        if int(data3[1]) == len(peers_list) - 1:
                            peers_list.pop(-1)

                            clt.send(f"P{len(peers_list) - 1};CONNECT_WITH;{peers_list[0]}|".encode("utf-8"))
                        # Caso o peer que saiu não seja nem o primeiro nem o ultimo da rede
                        elif data3[1] != "1":
                            #numero do peer que saiu
                            quit_number = int(data3[1])
                            peers_list.pop(quit_number)
                            
                            before_number = quit_number - 1

                            clt.send(f"P{before_number};CONNECT_WITH;{peers_list[quit_number]}|".encode("utf-8"))
                            clt.send(f"P{quit_number + 1};NEW_ID;{quit_number}|".encode("utf-8"))
                        # Caso o peer que saiu seja o primeiro da rede
                        elif data3[1] == "1":
                            peers_list.pop(1)
                            clt.close()
                            connect_to = peers_list[1]

                            clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            clt.connect(connect_to)
                            print("Conectado com o novo par")
                            clt.send(f"P2;NEW_ID;1|".encode("utf-8"))
                
                # Mensagem de busca de contato nas lista telefonicas
                elif(data1 == "SC"):
                    clt.send(f"{command}|".encode("utf-8"))

for i in range(3):
    Thread(target=tracker).start()
