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

# register of my ID to the Server
myID = input("Enter your ID: ")

to_Msg = "ID"+SEP+myID+SEP  # message format  ID:클라이언트ID:
s.send(to_Msg.encode())

# 사용법 안내 메시지를 한 번에 출력
print('\n=== 채팅 프로그램 사용법 ===')
print('1. 브로드캐스트: BR:전달할 메시지 입력')
print('2. 특정 사용자 메시지: TO:전달할 사용자ID:전달할 메시지 입력')
print('3. 파일 전송: FILE:전송될사용자ID:경로 입력')
print('4. AI 채팅: AICHAT:질문내용 입력')
print('5. 종료: Q 입력')
print('6. 채팅방 생성: ROOM:CREATE:방이름 입력')
print('7. 채팅방 참여: ROOM:JOIN:방이름 입력')
print('8. 채팅방 나가기: ROOM:LEAVE:방이름 입력')
print('9. 채팅방 메시지: RMSG:방이름:메시지 입력')
print('10. 채팅방 목록: RLIST 입력')
print('11. 채팅방 멤버 목록: RMEM:방이름 입력')
print('12. 대화 기록 조회: HISTORY:대상ID:날짜(YYYY-MM-DD) 입력')
print('13. 채팅 내역 저장: EXPORT:시작일(YYYY-MM-DD):종료일(YYYY-MM-DD) 입력')
print('14. 대화 내용 검색: SEARCH:검색어 입력')
print('========================\n')

# 폴더 생성
if not os.path.exists('History_files'):
    os.makedirs('History_files')
if not os.path.exists('log_files'):
    os.makedirs('log_files')

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
    elif code.upper() == "AICHAT":
        if len(tokens) < 2:
            print("AI 채팅 형식이 잘못되었습니다.")
            continue
        question = tokens[1]
        to_Msg = f"AICHAT{SEP}{myID}{SEP}{question}"
        s.send(to_Msg.encode())
    elif code.upper() == "ROOM":
        if len(tokens) != 3:
            print("방 명령어 형식이 잘못되었습니다.")
            continue
        action = tokens[1]
        roomname = tokens[2]
        to_Msg = f"ROOM{SEP}{myID}{SEP}{roomname}{SEP}{action}{SEP}"
        s.send(to_Msg.encode())
    elif code.upper() == "RMSG":
        if len(tokens) != 3:
            print("방 메시지 형식이 잘못되었습니다.")
            continue
        roomname = tokens[1]
        message = tokens[2]
        to_Msg = f"RMSG{SEP}{roomname}{SEP}{myID}{SEP}{message}{SEP}"
        s.send(to_Msg.encode())
    elif code.upper() == "RLIST":
        to_Msg = f"RLIST{SEP}{myID}{SEP}"
        s.send(to_Msg.encode())
    elif code.upper() == "RMEM":
        if len(tokens) != 2:
            print("방 멤버 목록 요청 형식이 잘못되었습니다.")
            continue
        roomname = tokens[1]
        to_Msg = f"RMEM{SEP}{myID}{SEP}{roomname}{SEP}"
        s.send(to_Msg.encode())
    elif code.upper() == "HISTORY":
        if len(tokens) != 3:
            print("대화 기록 조회 형식이 잘못되었습니다.")
            continue
        target = tokens[1]
        date = tokens[2]
        to_Msg = f"HISTORY{SEP}{myID}{SEP}{target}{SEP}{date}{SEP}"
        s.send(to_Msg.encode())
    elif code.upper() == "EXPORT":
        if len(tokens) != 3:
            print("채팅 내역 저장 형식이 잘못되었습니다.")
            continue
        start_date = tokens[1]
        end_date = tokens[2]
        to_Msg = f"EXPORT{SEP}{myID}{SEP}{start_date}{SEP}{end_date}{SEP}"
        s.send(to_Msg.encode())
    elif code.upper() == "SEARCH":
        if len(tokens) != 2:
            print("검색 형식이 잘못되었습니다.")
            continue
        keyword = tokens[1]
        to_Msg = f"SEARCH{SEP}{myID}{SEP}{keyword}{SEP}"
        s.send(to_Msg.encode())
    to_Msg = ''  # to_Msg 내용 초기화 Initialization

# close the socket
s.shutdown(socket.SHUT_RDWR)
s.close()
print('종료')