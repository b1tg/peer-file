"""
@author b1tg (https://b1tg.github.io)
@date 2022-03-03
@version 0.1
"""



from __future__ import print_function
import socket, threading,json
import tempfile
import hashlib
import os
from os import path
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

MAGIC = b"PEER"
PKG_FILE = b"FILE"
FILE_END = b"FILE_END"
JSON_END = b"JSON_END"

RECV_BUF_SIZE = 1024 * 1024

def file_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def handle_client(client_socket):
    
    request = client_socket.recv(1024)
    print("[*] Received: %s" % request)
    
    client_socket.send("ACK!")
    client_socket.close()
    
def xxx():
    while True:
        client, addr = server.accept()
        print("[*] Acepted connection from: %s:%d" % (addr[0],addr[1]))
        
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

def client_side(peer_addr, file_path):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)
    print("connecting to {}:{}".format(peer_addr, 19030))
    try:
        client.connect((peer_addr, 19030))
    except Exception as e:
        print("connect to {} error: {}".format(peer_addr, e))
        return
    print("connected!")
    client.send(MAGIC)    
    client.send(PKG_FILE)
    md5 = file_md5(file_path)
    with open(file_path) as f:
        data = f.read()
        data_len = len(data)
    head, tail = os.path.split(file_path)
    file_name = tail
    json_data = {
        "action":"recv",
        "filename":file_name,
        "size": data_len,
        "md5": md5,
    }
    client.send(json.dumps(json_data))
    client.send(JSON_END)
    if client.sendall(data) == None:
        print("[*] client send {}".format(len(data)))
    else:
        print("[*] client sendall failed")
    client.send(FILE_END)

def listen_side():
    server.bind(("0.0.0.0", 19030))
                
    server.listen(5)

    print("[*] Listening on :%d" % (19030))
    while True:
        client, addr = server.accept()
        print("[*] Acepted connection from: %s:%d" % (addr[0],addr[1]))

        magic = client.recv(len(MAGIC))
        if magic != MAGIC:
            print("[*] Bad magic...")
            client.close()
            continue
        print("[*] Right magic")
        pkg_file = client.recv(len(PKG_FILE))
        if pkg_file != PKG_FILE:
            print("[-] unsupport task {}".format(pkg_file))
            client.close()
            continue
        # data_len = client.recv(4) # recv int
        # print("[*] recv data_len={}".format(data_len))
        # data = client.recv(data_len)

        data = b''
        idx = 0
        retry = 0
        while idx <= 0: 
            print("[*] try parse json")
            new_data = client.recv(4096)
            data = data + new_data
            idx = data.find(JSON_END)
            # retry += 1
            # if retry > 10:
            #     print("[-] parse json err {}".format(e.__traceback__))
            #     client.close()

        try:
            data_json = json.loads(data[:idx])
            print("[*] recv data_json=\n%s" %data_json)
            action = data_json["action"]
            filename = data_json["filename"]
            size = data_json["size"]
            md5 = data_json["md5"]
        except Exception as e:
            print("[-] parse json err {}".format(e.__traceback__))
            client.close()
            continue         
        if action != "recv":
            print("[-] action not support")
            client.close()
            continue
        
        data_buf = data[idx+len(JSON_END):]
        recv_n = len(data_buf)
        print("[*] recv_n:{}, except_n:{}".format(recv_n, size+len(FILE_END)))
        while recv_n < size+len(FILE_END):
            recv_data = client.recv(RECV_BUF_SIZE)
            if len(recv_data) == 0:
                print("[*] warning: zero data")
                #break
            recv_n = recv_n + len(recv_data)
            data_buf = data_buf + recv_data
            #print("[*] recv_n:{}, except_n:{}, len:{}".format(recv_n, size+len(FILE_END), len(data_buf)))
            #print("{}/{} {}%".format(recv_n, size+len(FILE_END), recv_n*100/(size+len(FILE_END))))
            print("\r{}%".format(recv_n*100/(size+len(FILE_END))), end='')
            sys.stdout.flush()
        print()
        #idx = data_buf.find(FILE_END)  # this is bug if u send this file
        #print("[*] idx: {}".format(idx))
        data_buf = data_buf[:len(data_buf)-len(FILE_END)]
        #print("[*] data_buf %s"  % data_buf)
        tmp_dir = tempfile.mkdtemp()
        filepath = path.join(tmp_dir, filename)
        print("[*] filepath {}".format(filepath))
        with open(filepath, "wb") as f:
            f.write(data_buf)
        print("[*] success download file")
        md5_new = file_md5(filepath)
        if md5 != md5_new: 
            print("[-] md5 check failed, expect {}, get {}".format(md5, md5_new))
            client.close()
            continue
        print("[*] md5 check success") 
        client.close()

import sys
who = sys.argv[1]

if who=="listen":
    listen_side()
elif who=="client":
    client_side(sys.argv[2], sys.argv[3])
else:
    print("[-] unknown side")
