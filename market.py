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


def socket_handler(s, a , lockgain_wrt, lockgain_read):
    with s:
        print("Connected to client: ", a)
        data = s.recv(1024)
        m = data.decode()
        print(m)
        print(energyGain.value)
        lockgain_read.acquire()
        read_count.value += 1
        if (read_count.value == 1):
            lockgain_wrt.acquire()
        lockgain_read.release()
        energyGain.value = energyGain.value + float(m)
        print (energyGain.value)
        lockgain_read.acquire()
        read_count.value -= 1
        if (read_count.value == 0):
            lockgain_wrt.release()
        lockgain_read.release()
        resp = "okidoc"
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
                externalFactors[1][1] = 0
            else:
                print ("fin " + externalFactors[1][0])
                externalFactors[1][1] = 0
        case _:
            print("unknown signal")
    
def externalFunction():
    signalArray = [signal.SIGUSR1, signal.SIGUSR2]
    while True:
        time.sleep(5)
        os.kill(os.getppid(), random.choice(signalArray))

def transactionHandler(lockgain_wrt,lockgain_read):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setblocking(False)
        server_socket.bind((HOST, PORT))
        print("socket online")
        server_socket.listen(4)
        with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
            while True:
                readable, writable, error = select.select([server_socket], [], [], 1)
                if server_socket in readable:
                    client_socket, address = server_socket.accept()
                    executor.submit(socket_handler, client_socket, address, lockgain_wrt, lockgain_read, )

def priceCalculatorFunction(attenuationCoefficient, internalFactors, externalFactors, lockgain_wrt, lockPrice, lockTemperature):
    while True:
        time.sleep(10)
        
        print("Recomputing EnergyPrice")
        lockgain_wrt.acquire()
        lockPrice.acquire()
        lockTemperature.acquire()
        sumInternal = 0
        sumExternal = 0
        print("temperature: " + str(temperature.value))
        print("inverse temperature: " + str(inverseTemperature.value))
        print("new energyGain: " + str(energyGain.value))
        print("infrastructure status: " + str(externalFactors[0][1]))
        for x in internalFactors:
            sumInternal += x[0].value*x[1]
        for x in externalFactors:
            sumExternal =+ x[1]*x[2]

        energyPrice.value = attenuationCoefficient*energyPrice.value +sumInternal + sumExternal
        print("new energy price: " + str(energyPrice.value))
        energyGain.value = 0
        lockgain_wrt.release()
        lockPrice.release()
        lockTemperature.release()


        
if __name__ == "__main__":
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    lockgain_wrt  = threading.Lock()
    lockgain_read = threading.Lock()
    lockPrice = threading.Lock()
    lockTemperature = threading.Lock()
    energyGain = Value('f', 0)
    energyPrice = Value('f',0.1464)
    temperature = Value('f', 25)
    read_count = Value('d', 0)
    inverseTemperature = Value('f', temperature.value)
    attenuationCoefficient = 0.99
    internalFactors = [[inverseTemperature , 0.001],[energyGain,0.001]]
    externalFactors = [["infrastructures endommagées",0, 0.001],["taxe sur l'énergie", 0, 0.001]]
    HOST = "localhost"
    PORT = 1790
    
    weather = Process(target=weatherFunction, args=(lockTemperature,))
    weather.start()
    transaction = threading.Thread(target=transactionHandler, args = (lockgain_wrt, lockgain_read,))
    transaction.start()
    priceCalculator = threading.Thread(target = priceCalculatorFunction, args = (attenuationCoefficient, internalFactors, externalFactors, lockgain_wrt, lockPrice, lockTemperature))
    priceCalculator.start()
    external = Process(target=externalFunction, args=())
    external.start()
    external.join()