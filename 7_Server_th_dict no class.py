# server_thread dictionary exit
# 클라이언트로 부터 exit 문자열이 올때까지 계속 수신
# exit 문자열을 수신하면 while 문 탈출하여 연결종료

from socket import *    
from select import *
from threading import Thread

HOST = ''
PORT = 10000
BUFSIZE = 1024
ADDR = (HOST, PORT)

# 연결된 client의 소켓 집합 set of connected client sockets
clientSockets = {}  #dictionary 생성 방법
#threads = []
       
def msg_proc(cs, m):
    global clientSockets
    tokens = m.split(':')
    code = tokens[0]
    try:
        if (code.upper() == "ID"):
            print('reg id: ',m)
            clientSockets[tokens[1]] = cs   # client ID와 client 소켓값 저장
            cs.send("Success:Reg_ID".encode())
            return True
        elif (code.upper()  == "TO"):        
            fromID = tokens[1]
            toID = tokens[2]
            toMsg = tokens[3]
            print(f"1to1: From {1} To {2} Message {3}",fromID, toID, toMsg)
            toSocket = clientSockets.get(toID)  # 전달할 ID의 소켓 값 꺼내오기
            toSocket.send(m.encode())
            cs.send("Success:1to1".encode())
            return True
        elif (code.upper()  == "BR"):
            print('broadcast data: ', m)
            for socket in clientSockets.values(): # broadcast하기 위해 모든 소켓값 꺼내오기
                if (cs == socket):
                    cs.send("Success:BR".encode())
                else:
                    socket.send(m.encode())
            return True
        elif (code.upper()  == "QUIT"):
            fromID = tokens[1]
            clientSockets.pop(fromID)  #종료한 client 제거
            cs.close()
            print("Disconnected:{}", fromID)
            return False
    except Exception as e:
        print(f"서버와 연결 종료")
        return False
         
def client_com(cs):
    # 클라이언트로부터 id 메시지를 받음

    while True:
        try:  # 아래 문장 무조건 실행
            msg = cs.recv(BUFSIZE).decode()
            #print('recieve data : ',msg)
        except Exception as e:  # 위 문장 에러 처리: client no longer connected
            print(f"클라이언트와 연결 종료")
            for id, socket in clientSockets.items():
                if cs == socket:
                    clientSockets.pop(id)
            break
        else:  # recv 성공하면 메시지 처리
            if ( msg_proc(cs, msg) == False):
                break  # 클라이언트가 종료하면 루프 탈출 후 스레드 종료
        

def client_acpt():
    # 소켓 생성
    global serverSocket 
    serverSocket = socket(AF_INET, SOCK_STREAM) 
    #serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 즉시 재사용하기 위해
    ##     socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    # 소켓 주소 정보 할당
    serverSocket.bind(ADDR)

    # 연결 수신 대기 상태
    serverSocket.listen(10)
    print('대기')

    # 연결 수락
    while True:
        try:
            clientSocket, addr_info = serverSocket.accept()
            print('연결 수락: client 정보 ', addr_info)
            tc = Thread(target = client_com, args=(clientSocket,))
            tc.daemon = True
            tc.start()
            #threads.append(tc)
        except Exception as e:
            print(f"accept 종료")
            break
        
client_acpt()

msg = input() #키보드 입력하면 종료
# 소켓 종료
for socket in clientSockets.values():
    try:
            socket.shutdown(socket.SHUT_RDWR)
            socket.close()
    except Exception as e:
            continue
        
serverSocket.close()
print('종료')