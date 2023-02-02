import sysv_ipc
import sys, os, signal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
import subprocess
import socket
import time


host = "localhost"
port = 1790 

def window():
    app = QApplication(sys.argv)
    widget = QWidget()

    add = QPushButton(widget)
    add.setText("End simulation")
    add.move(20, 40)
    add.clicked.connect(killSimulation)

    widget.setGeometry(50,50,200,100)
    widget.setWindowTitle("Control panel")
    widget.show()
    
    os._exit(app.exec_())

def killSimulation():
    for i in range (1, 200):
        try:
            mq = sysv_ipc.MessageQueue(i)
            mq.remove()
            print("/!\/!\Queue ", i, " has been removed")
        except:
            pass
    time.sleep(1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try: 
            client_socket.connect((host, port))
            print("/!\/!\Control panel connected to server")
        except:
            print("/!\/!\Couldn't connect to server.")
        msg = "STOP"
        client_socket.send(msg.encode())
    print("/!\/!\Terminating simulation")
    sys.exit(1)

if __name__=="__main__":
    try:
        mq = sysv_ipc.MessageQueue(128, sysv_ipc.IPC_CREX)
        print("/!\/!\Successfully started queue 128")
    except:
        print("/!\/!\Message queue", 128, "already exsits, terminating.")
        os._exit(1)
    
    market = subprocess.Popen(['python3','market.py'], stdout=sys.stdout) 
    time.sleep(1)
   
    window()
