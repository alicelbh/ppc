import sys
from threading import Thread, Lock

import array
import time
import sysv_ipc
 
def produceEnergy(pR, s, n, mutex):
    while(True):
        time.sleep(pR)
        with mutex:
          #  print("/!\/!\Producing...")
            if s[0]>0:
                s[0]+=1
                print("Energy stock : ", s[0])
       # print("Producing over")
            

def consumeEnergy(cR, s, mutex):
    while(True):
        time.sleep(cR)
        with mutex:
           # print("/!\/!\Consuming...")
            if s[0]>0:
                s[0]-=1
                print("Energy stock : ", s[0])
        #print("Consuming over")

def energyTrade(n, s, mutex, c, p, msg_queue, k, pol):
    while(True):
        time.sleep(1)
        with mutex:
            if s[0]>n and c>p:
                print(".....Selling....")
                sell(n, s, msg_queue, pol)

            if s[0]<n and p>c:
                print(".....Buying.....")
                buy(n, s, msg_queue, k)

def sell(n, s, msg_queue, pol):
    buyerInterested = False
    if pol == "scrooge":
        print("Going to market")
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
        if buyerInterested==True:
            try:
                new_mq = sysv_ipc.MessageQueue(newKey)
                print("      Entered channel ", newKey)
                energySend = str(s[0]-n) #we give the amount of energy we have in excess
                new_mq.send(energySend.encode(),type=newKey)     
                s[0]-= s[0]-n
                print("         Post-trade stock : ", s[0], ".....")  
            except:
                #print(sys.exc_info()[0])
                print("      Buyer has retracted. Going back to main channel")
                sell(n, s, msg_queue)



def buy(n, s, msg_queue, k):
    try:
        msg = str(k).encode()
        msg_queue.send(msg, type=1)
        print("   Sent buying offer")
        new_mq = sysv_ipc.MessageQueue(k, sysv_ipc.IPC_CREX)
        time.sleep(1)
        m, t = new_mq.receive(False)
        print("      I received ", m.decode())
        s[0]+= int(m.decode()) 
        print("         Post-trade energy stock : ", s[0])  
        new_mq.remove()    

    except:
        e = sys.exc_info()[0]
        print("      No seller. Going to market")
        #print(e)
        new_mq.remove()
    time.sleep(3)




if __name__ == "__main__":
    if sys.argv[5]== "y":
        128
        try:
            mq = sysv_ipc.MessageQueue(128, sysv_ipc.IPC_CREX)
        except:
            print("Message queue", 128, "already exsits, terminating.")
            sys.exit(1)
    else:
        try:
            mq = sysv_ipc.MessageQueue(128)
        except:
            print("Cannot connect to message queue", 128, ", terminating.")
            sys.exit(1) 


        
    lock = Lock()

    initialProdRate = int(sys.argv[1])
    initialConsRate = int(sys.argv[2])
    key = int(sys.argv[3])
    policy = sys.argv[4]

    energyNeeds = 2 
    energyStock = array.array('i', range(1))
    energyStock[0] = 5

    production = Thread(target=produceEnergy, args=(initialProdRate,energyStock,energyNeeds, lock,))
    consumption = Thread(target=consumeEnergy, args=(initialConsRate,energyStock,lock,))
    trade = Thread(target=energyTrade, args=(energyNeeds, energyStock, lock, initialConsRate, initialProdRate, mq, key, policy))

    production.start()
    consumption.start()
    trade.start()
    production.join()
    consumption.join()
    trade.join()