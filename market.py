import os
import time
import signal
from multiprocessing import Process
from multiprocessing import Value
import threading
import random
import socket
import select
import concurrent.futures


def socket_handler(s, a , lockPrice_wrt, lockPrice_read, lockGain):
    with s:
        global serve
        print("")
        print("Connected to client: ", a)
        data = s.recv(1024)
        msg = data.decode()
        if(msg == "STOP"):
            serve = False
        else:
            text = msg.split()
            status = text[0]
            m = float(text[1])
            if (status == "buy"):
                m = -m    
            lockPrice_read.acquire()
            read_count.value += 1
            if (read_count.value == 1):
                lockPrice_wrt.acquire()
            lockPrice_read.release()
            lockGain.acquire()
            print("current energy balance: " + str(-energyGain.value))
            print("impending balance modification: " + str(m))
            energyGain.value = energyGain.value - m #we use a minus so that the price increases with the scarcity of energy
            print ("new balance: " + str(-energyGain.value))
            lockGain.release()
            if (status == "buy"):
                outcome = "cost"
            else:
                outcome = "yielded"

            message = "this transaction " + outcome +" you: " +"$" + str(abs(m)*energyPrice.value)
            #print(message)
            lockPrice_read.acquire()
            read_count.value -= 1
            if (read_count.value == 0):
                lockPrice_wrt.release()
            lockPrice_read.release()
            resp = message
            s.send(resp.encode())
        print("Disconnecting from client: ", a)
        


def weatherFunction(lockTemperature):
    while True:
        i = random.randint(-2,2)
        time.sleep(1)
        lockTemperature.acquire()
        temperature.value = temperature.value + i
        inverseTemperature.value = 1/temperature.value
        lockTemperature.release()
def handler(sig, frame):
    lockExternal.acquire()
    match sig:
        case signal.SIGUSR1:
            if (externalFactors[0][1]==0):
                print("début " + externalFactors[0][0])
                externalFactors[0][1] = 1
            else:
                print ("fin " + externalFactors[0][0])
                externalFactors[0][1] = 0
        case signal.SIGUSR2:
            if (externalFactors[1][1]==0):
                print("début " + externalFactors[1][0])
                externalFactors[1][1] = 1
            else:
                print ("fin " + externalFactors[1][0])
                externalFactors[1][1] = 0
        case _:
            print("unknown signal")
    lockExternal.release()

def externalFunction():
    signalArray = [signal.SIGUSR1, signal.SIGUSR2]
    while True:
        time.sleep(60)
        os.kill(os.getppid(), random.choice(signalArray))

def transactionHandler(lockPrice_wrt,lockPrice_read, lockGain):
    n = 6
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setblocking(False)
        server_socket.bind((HOST, PORT))
        print("socket online")
        server_socket.listen(n)
        with concurrent.futures.ThreadPoolExecutor(max_workers = n) as executor:
            while serve:
                readable, writable, error = select.select([server_socket], [], [], 1)
                if server_socket in readable:
                    client_socket, address = server_socket.accept()
                    executor.submit(socket_handler, client_socket, address, lockPrice_wrt, lockPrice_read, lockGain, )
    #os.kill(os.getppid(), signal.SIGKILL)

def priceCalculatorFunction(attenuationCoefficient, internalFactors, externalFactors, lockPrice_wrt, lockTemperature, lockExternal, lockGain):
    while True:
        time.sleep(10)
        os.system('clear')
        print("***\nRecomputing EnergyPrice\n***")
        lockPrice_wrt.acquire()
        lockTemperature.acquire()
        lockExternal.acquire()
        lockGain.acquire()
        sumInternal = 0
        sumExternal = 0
        print("temperature: " + str(temperature.value))
        #print("inverse temperature: " + str(inverseTemperature.value))
        print("net sum of energy gained through transactions: " + str(energyGain.value))
        print("current external events:")
        for i in externalFactors:
            if (i[1] == 1):
                print(i[0])

        for x in internalFactors:
            sumInternal += x[0].value*x[1]
        for x in externalFactors:
            sumExternal =+ x[1]*x[2]

        energyPrice.value = attenuationCoefficient*energyPrice.value +sumInternal + sumExternal
        print("new energy price: " + str(energyPrice.value))
        energyGain.value = 0
        lockPrice_wrt.release()
        lockTemperature.release()
        lockExternal.release()
        lockGain.release()


        
if __name__ == "__main__":
    serve = True
    os.system('clear')
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    lockPrice_wrt  = threading.Lock()
    lockPrice_read = threading.Lock()
    lockTemperature = threading.Lock()
    lockExternal = threading.Lock()
    lockGain = threading.Lock()
    energyGain = Value('f', 0)
    energyPrice = Value('f',0.1464)
    temperature = Value('f', 25)
    read_count = Value('d', 0)
    inverseTemperature = Value('f', temperature.value)
    attenuationCoefficient = 0.99
    internalFactors = [[inverseTemperature , 0.001],[energyGain,0.00001]]
    externalFactors = [["infrastructures endommagées",0, 0.001],["taxe sur l'énergie", 0, 0.001]]
    HOST = "localhost"
    PORT = 1790
    
    weather = Process(target=weatherFunction, args=(lockTemperature,))
    weather.start()
    transaction = threading.Thread(target=transactionHandler, args = (lockPrice_wrt, lockPrice_read, lockGain,))
    transaction.start()
    priceCalculator = threading.Thread(target = priceCalculatorFunction, args = (attenuationCoefficient, internalFactors, externalFactors, lockPrice_wrt, lockTemperature, lockExternal, lockGain))
    priceCalculator.start()
    external = Process(target=externalFunction, args=())
    external.start()
    transaction.join()