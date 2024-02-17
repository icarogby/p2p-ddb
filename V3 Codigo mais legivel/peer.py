import socket
from threading import Thread
import os
from time import sleep

PEER_PORT = 9902
TRACKER_PORT = 9902

# Peer IP address
peerIp = socket.gethostbyname(socket.gethostname())
peerPort = PEER_PORT

# Tracker IP address
trackerIp = input("Write the tracker's IP address:")
trackerPort = TRACKER_PORT

# Global variables
id = 0 # Peer ID
contactList = {} #TODO Save on DB
searchedName = "" # Name searched by the user
connectTo = (trackerIp, trackerPort) # First connection is with the tracker

# Server socket
svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
svr.bind((peerIp, peerPort))
svr.listen(5)

# Client socket
clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clt.connect(connectTo)

# Send the peer's IP and port to the tracker
clt.send(f"ID;{peerIp};{peerPort}".encode("utf-8")) #TODO chance protocol

def peer():
    global id
    global connectTo
    global svr, clt
    global contactList

    while True:
        # Accept connection from the server side
        con, _ = svr.accept()

        while True:
            # Receive data from the server
            data = con.recv(1024)
            commands = data.decode("utf-8")

            # If the connection is loss, break the loop and waits for a new connection
            if not data:
                break
            
            #TODO chance protocol
            for command in commands.split("|"):
                if command == "":
                    continue
                
                # data1 = Destino | data2 = Comando | data3 = Informação personalizada
                data1, data2, data3 = command.split(";")

                # Caso a mensagem seja para o novo peer
                if (data1 == "ID"):
                    if id == 0:
                        id = data3
                    else:
                        clt.send(f"{command}|".encode("utf-8")) # Envia a mensagem para frente

                # Caso a mesagem recebida for para um peer
                elif data1[0] == f"P":
                    # Se o peer não for o destino, repassa a mensagem
                    if data1 != f"P{id}":
                        clt.send(f"{command}|".encode("utf-8"))

                    # Se o peer for o destino, executa o comando
                    elif data1 == f"P{id}":
                        # Fecha a conexão com o peer anterior e conecta com o novo
                        if data2 == "CONNECT_WITH":
                            # Fecha conexão
                            clt.close()
                            
                            # Converte de string para tupla
                            con_tuple = data3.split(",")
                            ip_addr = con_tuple[0][2:-1]
                            port_addr = int(con_tuple[1][1:-1])

                            # Abre nova conexão
                            connect_to = (ip_addr, port_addr)
                            clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            clt.connect(connect_to)

                        # Recebe um novo id e manda o proximo peer atualizar também
                        elif data2 == "NEW_ID":
                            id = int(data3)
                            data3 = id + 1
                            clt.send(f"P{int(data1[1])+1};{data2};{data3}|".encode("utf-8"))
                        
                        # O contato buscado foi encontrado e é adicionado na agenda
                        elif data2 == "FINDED":
                            print(f"Contato encontrado: {data3}")
                            contactList[name] = data3
                
                # Caso a mensagem recebida for de busca
                elif data1 == "SC":
                        # Se eu tiver o contato, envia para o peer que pediu
                        if data3 in contactList:
                            clt.send(f"{data2};FINDED;{contactList[data3]}|".encode("utf-8"))
                        else:
                            if data2 == f"P{id}":
                                print("Contato não encontrado")
                            else:
                                clt.send(f"{command}|".encode("utf-8"))
                
                # Caso a mensagem recebida for para o tracker
                elif data1 == "TK":
                    clt.send(f"{command}Z".encode("utf-8"))
                        
# Função para interagir com o usuário
def user_commands():
    global clt
    global name
    valid_commands = [1, 2, 3, 4, 5]

    while True:
        print("\nLISTA TELEFONICA")
        print("1 - Adicionar contato")
        print("2 - Listar meus contatos")
        print("3 - Buscar contato")
        print("4 - Meu ID")
        print("5 - Sair da rede")
        
        ipt = input("\nDigite o comando: ")

        try:
            ipt = int(ipt)
        except:
            print("Digite um comando válido")
            continue

        if (ipt not in valid_commands):
            print("Digite um comando válido")
            continue

        if ipt == 1:
            name = input("Nome: ")
            number = input("Número: ")

            contactList[name] = number
            print("\nContato salvo")
        
        elif ipt == 2:
            print(contactList)
        
        elif ipt == 3:
            name = input("Nome: ")
            
            if name in contactList:
                print(contactList[name])
            else:
                clt.send(f"SC;P{id};{name}".encode("utf-8"))
                sleep(2)
        
        elif ipt == 4:
            print(id)
        
        elif ipt == 5:
            clt.send(f"TK;REMOVE_FROM_LIST;P{id}".encode("utf-8"))

            clt.close()
            svr.close()
            
            print("programa fechado")
            os._exit(0)

Thread(target=peer).start()
Thread(target=user_commands).start()
