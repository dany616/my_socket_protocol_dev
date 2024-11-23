#client ID BR TO Q
import socket
from threading import Thread
import sys
import os

# server's IP address
# if the server is not on this machine, 
# put the private (network) IP address (e.g 192.168.1.2)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 10000 # server's port
BUF_SIZE = 1024
SEP = ":" # we will use this to separate the client name & message

# initialize TCP socket
s = socket.socket()
print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}...")
# connect to the server
try:
    s.connect((SERVER_HOST, SERVER_PORT))
except Exception as e:
    print("서버와 연결 종료_connect")
    sys.exit()
    
print("서버와 연결")

def listen_for_messages():  # receive 전용 Thread에서 수행하는 함수
    while True:
        try:
            message = s.recv(BUF_SIZE).decode()
            print("\n" + message)
        except Exception as e:
            print("서버와 연결 종료_recv")
            return

# make a thread that listens for messages to this client
t = Thread(target=listen_for_messages)
# make the thread daemon so it ends whenever the main thread ends
t.daemon = True
# start the thread
t.start()

# register of my ID to the Server
myID = input("Enter your ID: ")

to_Msg = "ID"+SEP+myID+SEP  # message format  ID:클라이언트ID:
s.send(to_Msg.encode())
print('사용법: 브로드캐스트하려면 BR:전달할 메시지 입력')
print('      : 특정 사용자에 전달 하려면 TO:전달할 사용자ID:전달할 메시지 입력')
print('      : 파일 전송하려면 FILE:전송될사용자ID:경로 입력')
print('      : 종료하려면 Q 입력')

while True:
    # input message we want to send to the server
    msg =  input()
    tokens = msg.split(SEP)
    code = tokens[0]
    # a way to exit the program
    if code.upper() == 'Q':
        to_Msg = "Quit"+SEP+myID+SEP
        s.send(to_Msg.encode())
        break
    elif code.upper()  == "BR" :
        to_Msg = code + SEP + myID + SEP + tokens[1] + SEP
        s.send(to_Msg.encode())
    elif code.upper() == "TO":
        to_Msg = code + SEP + myID + SEP + tokens[1] + SEP + tokens[2] + SEP
        s.send(to_Msg.encode())
    elif code.upper() == "FILE":
        if len(tokens) < 3:
            print("파일 전송 형식이 잘못되었습니다.")
            continue
        recipient_id = tokens[1]
        file_path = tokens[2]
        
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            to_Msg = f"FILE{SEP}{myID}{SEP}{recipient_id}{SEP}{os.path.basename(file_path)}{SEP}{file_size}"
            s.send(to_Msg.encode())
            
            with open(file_path, 'rb') as f:
                bytes_read = f.read(BUF_SIZE)
                while bytes_read:
                    s.send(bytes_read)
                    bytes_read = f.read(BUF_SIZE)
            print("파일 전송 완료")
        else:
            print("파일이 존재하지 않습니다.")
    to_Msg = ''  # to_Msg 내용 초기화 Initialization

# close the socket
s.shutdown(socket.SHUT_RDWR)
s.close()
print('종료')