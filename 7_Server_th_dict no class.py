# server_thread dictionary exit
# 클라이언트로 부터 exit 문자열이 올때까지 계속 수신
# exit 문자열을 수신하면 while 문 탈출하여 연결종료

from socket import *    
from select import *
from threading import Thread
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

HOST = ''
PORT = 10000
BUFSIZE = 1024
ADDR = (HOST, PORT)

# 연결된 client의 소켓 집합 set of connected client sockets
clientSockets = {}  #dictionary 생성 방법
#threads = []
       
# OpenAI 클라이언트 초기화
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.upstage.ai/v1/solar"
)

# 파일 상단에 전역 변수 추가
chatRooms = {}  # {방이름: {'owner': 방장ID, 'members': set(멤버ID들)}}

def get_ai_response(message):
    try:
        response = client.chat.completions.create(
            model="solar-pro",
            messages=[{"role": "user", "content": message}],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 응답 오류: {str(e)}"

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
        elif (code.upper()  == "FILE"):
            fromID = tokens[1]
            toID = tokens[2]
            file_name = tokens[3]
            file_size = int(tokens[4])
            print(f"파일 수신: {file_name} from {fromID} to {toID}, 크기: {file_size} 바이트")

        
            
            # 수신할 폴더 생성
            if not os.path.exists('received_files'):
                os.makedirs('received_files')
            
            with open(os.path.join('received_files', file_name), 'wb') as f:
                bytes_received = 0
                while bytes_received < file_size:
                    bytes_data = cs.recv(BUFSIZE)
                    if not bytes_data:
                        break
                    f.write(bytes_data)
                    bytes_received += len(bytes_data)
            print(f"파일 수신 완료: {file_name} 경로: received_files/{file_name}")
            return True
        elif (code.upper() == "AICHAT"):
            fromID = tokens[1]
            question = tokens[2]
            print(f"AI 채팅 요청: {fromID} - {question}")
            
            ai_response = get_ai_response(question)
            response_msg = f"AICHAT:{fromID}:AI 응답: {ai_response}"
            cs.send(response_msg.encode())
            return True
        elif (code.upper() == "ROOM"):
            fromID = tokens[1]
            roomname = tokens[2]
            action = tokens[3].upper()
            
            if action == "CREATE":
                if roomname in chatRooms:
                    cs.send(f"Error:방 '{roomname}'이 이미 존재합니다.".encode())
                else:
                    chatRooms[roomname] = {'owner': fromID, 'members': {fromID}}
                    cs.send(f"Success:방 '{roomname}'이 생성되었습니다.".encode())
            elif action == "JOIN":
                if roomname not in chatRooms:
                    cs.send(f"Error:방 '{roomname}'이 존재하지 않습니다.".encode())
                else:
                    chatRooms[roomname]['members'].add(fromID)
                    cs.send(f"Success:방 '{roomname}'에 참여했습니다.".encode())
            elif action == "LEAVE":
                if roomname in chatRooms and fromID in chatRooms[roomname]['members']:
                    chatRooms[roomname]['members'].remove(fromID)
                    if len(chatRooms[roomname]['members']) == 0:
                        del chatRooms[roomname]
                    cs.send(f"Success:방 '{roomname}'에서 나갔습니다.".encode())
                else:
                    cs.send(f"Error:방 '{roomname}'에 속해있지 않습니다.".encode())
            return True
            
        elif (code.upper() == "RMSG"):
            roomname = tokens[1]
            fromID = tokens[2]
            message = tokens[3]
            
            if roomname in chatRooms and fromID in chatRooms[roomname]['members']:
                room_message = f"RMSG:{roomname}:{fromID}:{message}"
                for member_id in chatRooms[roomname]['members']:
                    if member_id != fromID:
                        clientSockets[member_id].send(room_message.encode())
                cs.send("Success:방 메시지를 전송했습니다.".encode())
            else:
                cs.send(f"Error:방 '{roomname}'에 속해있지 않습니다.".encode())
            return True
            
        elif (code.upper() == "RLIST"):
            fromID = tokens[1]
            room_list = "채팅방 목록:\n" + "\n".join([f"- {room} (멤버 수: {len(members['members'])})" 
                                                for room, members in chatRooms.items()])
            cs.send(room_list.encode())
            return True
            
        elif (code.upper() == "RMEM"):
            fromID = tokens[1]
            roomname = tokens[2]
            
            if roomname in chatRooms:
                member_list = f"방 '{roomname}' 멤버 목록:\n" + "\n".join(chatRooms[roomname]['members'])
                cs.send(member_list.encode())
            else:
                cs.send(f"Error:방 '{roomname}'이 존재하지 않습니다.".encode())
            return True
    except Exception as e:
        print(f"서버와 연결 종료: {e}")
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
            print(f"accept 종료: {e}")
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