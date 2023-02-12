import socket
from threading import Thread
from random import randint
from time import sleep

# Endereço desse peer
peer_ip = socket.gethostbyname(socket.gethostname())
peer_port = randint(2001, 9999)

tracker_port = 2000

# ID do peer
id = 0
# Lista de contatos desse peer
contact_list = {}
name = ""

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

def peer():
    global id
    global connect_to
    global clt
    global contact_list

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

                print(f"Comando recebido pelo peer: {command}")
                
                # data1 = Destino | data2 = Comando | data3 = Informação personalizada
                data1, data2, data3 = command.split(";")

                # ID de quanto entra na rede, mas pode mudar depois
                if (data1 == "ID"):
                    if id == 0:
                        id = data3
                    else:
                        clt.send(f"{command}|".encode("utf-8"))

                # Caso a mesagem recebida for para um peer. Se for para esse peer,
                # executa o comando, se não, repassa para o proximo peer
                elif data1[0] == f"P":
                    if data1 != f"P{id}":
                        clt.send(f"{command}|".encode("utf-8"))

                    elif data1 == f"P{id}":
                        # Atualiza a conexao do lado cliente
                        if data2 == "CONNECT_WITH":
                            clt.close()

                            debug1 = data3.split(",")
                            debug2 = debug1[0][2:-1]
                            debug3 = int(debug1[1][1:-1])

                            connect_to = (debug2, debug3)
                            print(f"Conectando com {connect_to}")
                            clt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            clt.connect(connect_to)

                        # Recebe um novo id e manda o proximo peer atualizar também
                        if data2 == "NEW_ID":
                            id = int(data3)
                            data3 = id + 1
                            clt.send(f"P{int(data1[1])+1};{data2};{data3}|".encode("utf-8"))
                        
                        if data2 == "FINDED":
                            print(f"Contato encontrado: {data3}")
                            contact_list[name] = data3
                
                # Caso a mensagem recebida for de busca
                elif data1 == "SC":
                        if data3 in contact_list:
                            clt.send(f"{data2};FINDED;{contact_list[data3]}|".encode("utf-8"))
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

    while True:
        print("\nLISTA TELEFONICA")
        print("1 - Adicionar contato")
        print("2 - Listar contatos")
        print("3 - Buscar contato")
        print("4 - Meu ID")
        print("5 - Meus pares")
        print("6 - Sair da rede")
        
        command = int(input("\nDigite o comando: "))

        if command == 1:
            name = input("Nome: ")
            number = input("Número: ")

            contact_list[name] = number
            print("\nContato salvo")
        
        if command == 2:
            print(contact_list)
        
        if command == 3:
            name = input("Nome: ")
            
            if name in contact_list:
                print(contact_list[name])
            else:
                clt.send(f"SC;P{id};{name}".encode("utf-8"))
                sleep(2)
        
        if command == 4:
            print(id)
        
        if command == 5:
            print(connect_to)
        if command == 6:
            clt.send(f"TK;REMOVE_FROM_LIST;P{id}".encode("utf-8"))
            clt.close()
            svr.close()
            print("program closed")
        else:
            print("Comando inválido")

Thread(target=peer).start()
Thread(target=user_commands).start()
