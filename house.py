import sys
from threading import Thread, Lock

import array
import time
import sysv_ipc
import sys, os
import socket

def produceEnergy(pR, s, n, mutex):
    while(True):
        time.sleep(pR)
        with mutex:
          #  print("/!\/!\Producing...")
            if s[0]>0:
                s[0]+=1
                print("Energy stock : ", s[0])
            else:
                print("The house has reached its energy limit and is not functionning until it received energy.")
                
       # print("Producing over")
            
def consumeEnergy(cR, s, mutex):
    while(True):
        time.sleep(cR)
        with mutex:
           # print("/!\/!\Consuming...")
            if s[0]>0:
                s[0]-=1
                print("Energy stock : ", s[0])
            else:
                print("The house has reached its energy limit and is not functionning until it received energy.")

def energyTrade(n, s, mutex, c, p, msg_queue, k, pol, host, port):
    while(checkQueueExistence(128)):
        time.sleep(1)
        with mutex:
            if s[0]>n and c>p:
                print(".....Selling....")
                sell(n, s, msg_queue, pol, host, port)

            if s[0]<n and p>c:
                print(".....Buying.....")
                buy(n, s, msg_queue, k, host, port)


def sell(n, s, msg_queue, pol, host, port):
    buyerInterested = False
    if pol == "scrooge":
        print("Going to market")
        market(host, port, n, s)
    else:
        try:
            m, t = msg_queue.receive(False, type=1)
            newKey = int(m.decode())
            print("   Buyer offer on channel ", newKey)
            buyerInterested = True
        except:
            #print(sys.exc_info()[0])
            if pol == "generous":
                print(   "No buyer for now. Going back to main channel")
            if pol == "normal":
                print("   No buyer. Going to market")
                market(host, port, n, s)
        if buyerInterested==True:
            try:
                new_mq = sysv_ipc.MessageQueue(newKey)
                print("      Entered channel ", newKey)
                if new_mq.current_messages==0:
                    energySend = str(s[0]-n) #we give the amount of energy we have in excess
                    new_mq.send(energySend.encode(),type=newKey)     
                    s[0] = n
                    print("         Post-trade stock : ", s[0], ".....")
                else:
                    print("     Someone has already sent electricity. Going back to main channel")  
            except:
                #print(sys.exc_info()[0])
                print("      Buyer has retracted. Going back to main channel")
                sell(n, s, msg_queue, pol, host, port)


def buy(n, s, msg_queue, k, host, port):
    try:
        msg = str(k).encode()
        msg_queue.send(msg, type=1)
        print("   Sent buying offer")
        new_mq = sysv_ipc.MessageQueue(k, sysv_ipc.IPC_CREX)
        time.sleep(2)
        m, t = new_mq.receive(False)
        print("      I received ", m.decode())
        s[0]+= int(m.decode()) 
        print("         Post-trade energy stock : ", s[0])  
        new_mq.remove()    
    except:
        print("      No seller. Going to market")
        #print(e)
        if(checkQueueExistence(k)):
            new_mq.remove()
        market(host, port, n, s)


def market(host, port, n, s):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try: 
            client_socket.connect((host, port))
        except: 
            print("   Connection to market refused.")
            return 0
        print("   Trading " + str(n-s[0]))
        data = str(n-s[0])
        client_socket.send(data.encode())
        resp = client_socket.recv(1024)
        if not len(resp):
            print("The socket connection has been closed!")
            return 0
        print("   Market response:", resp.decode())
        s[0] = n 
        print("   Post-trade stock: " + str(s[0]))


def checkQueueExistence(key):
    try:
        test = sysv_ipc.MessageQueue(key)
        return True
    except:
        print(sys.exc_info()[0])
        return False
        

def checkMainQueue():
    while(True):
        time.sleep(1)
        try:
            test = sysv_ipc.MessageQueue(128)
        except:
            print("Simulation closed")
            os._exit(1)


if __name__ == "__main__":
    try:
        mq = sysv_ipc.MessageQueue(128)
    except:
        print("Cannot connect to message queue", 128, ", terminating.")
        sys.exit(1) 

    HOST = "localhost"
    PORT = 1790 
        
    lock = Lock()

    initialProdRate = int(sys.argv[1])
    initialConsRate = int(sys.argv[2])
    key = int(sys.argv[3])
    policy = sys.argv[4]

    energyNeeds = 4
    energyStock = array.array('i', range(1))
    energyStock[0] = 5

    production = Thread(target=produceEnergy, args=(initialProdRate,energyStock,energyNeeds, lock,))
    consumption = Thread(target=consumeEnergy, args=(initialConsRate,energyStock,lock,))
    trade = Thread(target=energyTrade, args=(energyNeeds, energyStock, lock, initialConsRate, initialProdRate, mq, key, policy, HOST, PORT))
    check = Thread(target=checkMainQueue)

    production.start()
    consumption.start()
    trade.start()
    check.start()
    production.join()
    consumption.join()
    trade.join()
    check.join()
