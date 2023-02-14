import socket
from threading import Thread, Lock
import os
from random import randint
from time import sleep
import logging
import sys
# from multiprocessing import Lock

# Endereço IP desse peer
try:
    peer_ip = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close())
               for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
except:
    enter = input("Erro ao tentar obter o endereço IP. Digite enter para sair.")
    os._exit(0)

tracker_port = 2000 # porta do tracker
peer_port = randint(2001, 9999) # porta desse peer
id = 0 # ID do peer
file_list = [] # Lista de arquivos desse peer
file_name = "" # Nome do arquivo buscado

print(f"PAR DA REDE")
print(f"IP: {peer_ip} PORT: {peer_port}")

tracker_ip = input("Digite o endereço ip do super nó: ")
connect_to = (tracker_ip, tracker_port)

# Socket servidor
svr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
svr.bind((peer_ip, peer_port))
svr.listen(5)

# Socket cliente ja envia mensagem de identificação
clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clt.connect((tracker_ip, tracker_port))
clt.send(f"ID;{peer_ip};{peer_port}".encode("utf-8"))

def encodeToUpload(nome_do_arquivo):
    name_file = nome_do_arquivo
    md = os.stat(name_file)

    lock = Lock()

    with lock:
        try:
            file = open(name_file, 'rb')
            data_out = bytes(file.read())
            file.close()
        except IOError as exc:
            logging.error(exc)
            return

    return str(data_out)

def decodeToDownload(name_file, binario=""):
    lock = Lock()
    lock.acquire()
    
    try:
        file = open(name_file, 'wb+')
        
        file.write(binario.encode("utf-8"))

        file.close()
    except IOError as exc:
        logging.error(exc)
    
    lock.release()

    print("Baixado com sucesso")


def peer():
    global id
    global connect_to
    global clt
    global file_list
    global file_name

    while True:
        # Aceita conexão pelo lado servidor
        con, adr = svr.accept()

        while True:
            #recebe a mensagem do peer anterior ou tracker
            data = con.recv(1024)
            commands = data.decode("utf-8")

            # Se uma conexão for fechada, sai do loop e espera uma nova conexão
            if not data:
                break
            
            # Separa e executa os comandos
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
                        clt.send(f"{command}|".encode("utf-8"))

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
                            print(f"Arquivo encontrado")
                            decodeToDownload(file_name, data3)
                            file_list.append(file_name)
                
                # Caso a mensagem recebida for de busca
                elif data1 == "SC":
                        # Se eu tiver o contato, envia para o peer que pediu
                        if data3 in file_list:
                            data = encodeToUpload(data3)
                            clt.send(f"{data2};FINDED;{data}|".encode("utf-8"))
                        else:
                            if data2 == f"P{id}":
                                print("arquivo não encontrado")
                            else:
                                clt.send(f"{command}|".encode("utf-8"))
                
                # Caso a mensagem recebida for para o tracker
                elif data1 == "TK":
                    clt.send(f"{command}Z".encode("utf-8"))
                        
# Função para interagir com o usuário
def user_commands():
    global clt
    global name
    global file_list
    valid_commands = [1, 2, 3, 4, 5]

    while True:
        print("\nLISTA TELEFONICA")
        print("1 - Adicionar arquivo")
        print("2 - Listar meus aquivos")
        print("3 - Buscar arquivo")
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
            file_name = input("Nome do arquivo: ")

            file_list.append(file_name)
            print("\nArquivo salvo na lista")
        
        elif ipt == 2:
            print(file_list)
        elif ipt == 3:
            file_name = input("Digite o nome do arquivo: ")
            
            if file_name in file_list:
                print("Você já tem esse arquivo.")
            else:
                clt.send(f"SC;P{id};{file_name}".encode("utf-8"))
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
