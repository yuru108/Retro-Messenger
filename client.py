import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(client):
    """接收來自 server 的訊息"""
    while True:
        try:
            message = client.recv(1024)
            if message:
                print(f"\n{message.decode('utf-8')}")
            else:
                raise Exception("伺服器中斷連線")
        except:
            print("與伺服器的連線已斷開")
            client.close()
            break

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    print("成功連接至伺服器")
    response = client.recv(1024).decode('utf-8')
    username = input(response)
    client.send(username.encode('utf-8'))

    threading.Thread(target=receive_messages, args=(client,)).start()

    while True:
        target_uid = input("輸入目標 UID (或 'quit' 離開): ")
        if target_uid.lower() == 'quit':
            client.close()
            break
        message = input("輸入訊息: ")
        client.send(f"{target_uid}|{message}".encode('utf-8'))

if __name__ == "__main__":
    main()