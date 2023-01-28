import sysv_ipc
import sys, os, signal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
import subprocess

try:
    mq = sysv_ipc.MessageQueue(128, sysv_ipc.IPC_CREX)
    print("Successfully started queue 128")
except:
    print("Message queue", 128, "already exsits, terminating.")
    sys.exit(1)

market = subprocess.Popen(['python3','market2.py'], stdout=sys.stdout)



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
            print("Queue ", i, " has been removed")
        except:
            #print(i, " doesn't exist")
            pass
    print("Terminating simulation")
    os.killpg(os.getpgid(market.pid), signal.SIGTERM)

window()
