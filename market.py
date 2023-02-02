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
from multiprocessing import set_start_method
set_start_method("fork")

class colors:
    MAGENTA = '\033[95m'
    YELLOW = '\033[93;1m'
    CYAN = '\033[96m'
    GREEN= '\033[92m'
    RED = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def socket_handler(s, a , lockPrice_wrt, lockPrice_read, lockGain):
    with s:
        global serve
        global energyGain
        global energyPrice
        global read_count
        print("")
        print(colors.MAGENTA + "Connected to client: " + str(a) + colors.ENDC)
        data = s.recv(1024)
        msg = data.decode()
        print("   " + msg)
        if(msg == "STOP"):
            serve = False
        else:
            text = msg.split()
            status = text[0]
            m = float(text[1])
            if (status == "buy"):
                m = -m    
            lockPrice_read.acquire()
            read_count += 1
            if (read_count == 1):
                lockPrice_wrt.acquire()
            lockPrice_read.release()
            lockGain.acquire()
            print("   Current energy balance: " + str(energyGain))
            print("   Impending balance modification: " + str(m))
            energyGain = energyGain + m 
            print ("   New balance: " + str(energyGain))
            lockGain.release()
            if (status == "buy"):
                outcome = "cost"
            else:
                outcome = "yielded"

            message = "this transaction " + outcome +" you: " +"$" + str(abs(m)*energyPrice)
            #print(message)
            lockPrice_read.acquire()
            read_count -= 1
            if (read_count == 0):
                lockPrice_wrt.release()
            lockPrice_read.release()
            resp = message
            s.send(resp.encode())
        print("   Disconnecting from client: ", a)
        


def weatherFunction(lockTemperature):
    while True:
        i = random.randint(-2,2)
        time.sleep(1)
        lockTemperature.acquire()
        temperature.value = temperature.value + i
        lockTemperature.release()
def handler(sig, frame):
    lockExternal.acquire()
    match sig:
        case signal.SIGUSR1:
            if (externalFactors[0][1]==0):
                print(colors.BOLD + "Start of " + externalFactors[0][0] + colors.ENDC)
                externalFactors[0][1] = 1
            else:
                print (colors.BOLD + "End of " + externalFactors[0][0] + colors.ENDC)
                externalFactors[0][1] = 0
        case signal.SIGUSR2:
            if (externalFactors[1][1]==0):
                print(colors.BOLD + "Start of " + externalFactors[1][0] + colors.ENDC)
                externalFactors[1][1] = 1
            else:
                print (colors.BOLD + "End of " + externalFactors[1][0] + colors.ENDC)
                externalFactors[1][1] = 0
        case signal.SIGTERM:
            os.kill(weather.pid, signal.SIGKILL)
            os.kill(external.pid, signal.SIGKILL)
            print(colors.RED + "Children terminated." + colors.ENDC)
            os.kill(os.getpid(), signal.SIGKILL)
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
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setblocking(False)
            server_socket.bind((HOST, PORT))
            print(colors.BOLD + "Socket online" + colors.ENDC)
            server_socket.listen(n)
            with concurrent.futures.ThreadPoolExecutor(max_workers = n) as executor:
                while serve:
                    readable, writable, error = select.select([server_socket], [], [], 1)
                    if server_socket in readable:
                        client_socket, address = server_socket.accept()
                        executor.submit(socket_handler, client_socket, address, lockPrice_wrt, lockPrice_read, lockGain, )
        os.kill(os.getpid(), signal.SIGTERM)
    except:
        print("Port is not ready yet")
        os.kill(os.getpid(), signal.SIGTERM)

def priceCalculatorFunction(attenuationCoefficient, internalFactors, externalFactors, lockPrice_wrt, lockTemperature, lockExternal, lockGain):
    while True:
        global energyGain
        global energyPrice
        time.sleep(10)
        #os.system('clear')
        print(colors.YELLOW + "***\nRecomputing energy price\n***" + colors.ENDC)
        lockPrice_wrt.acquire()
        lockTemperature.acquire()
        lockExternal.acquire()
        lockGain.acquire()
        sumInternal = 0
        sumExternal = 0
        if(temperature.value!=0):
            internalFactors[0][0] = 1/temperature.value
        internalFactors[1][0] = -energyGain
        print("   Temperature: " + str(temperature.value))
        print("   Net sum of energy gained through transactions: " + str(energyGain))
        print("   Current external events:")
        for i in externalFactors:
            if (i[1] == 1):
                print("   " + i[0])

        for x in internalFactors:
            sumInternal += x[0]*x[1]
        for x in externalFactors:
            sumExternal =+ x[1]*x[2]

        energyPrice = attenuationCoefficient*energyPrice +sumInternal + sumExternal
        print(colors.RED + "   New energy price: " + str(energyPrice) + colors.ENDC)
        energyGain = 0
        lockPrice_wrt.release()
        lockTemperature.release()
        lockExternal.release()
        lockGain.release()


        
if __name__ == "__main__":
    global serve
    serve = True
    #os.system('clear')
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)
    signal.signal(signal.SIGTERM, handler)
    lockPrice_wrt  = threading.Lock()
    lockPrice_read = threading.Lock()
    lockTemperature = threading.Lock()
    lockExternal = threading.Lock()
    lockGain = threading.Lock()
    global energyGain
    energyGain = 0
    global energyPrice
    energyPrice = 0.1464
    temperature = Value('f', 25)
    global read_count
    read_count = 0
    global inverseTemperature
    inverseTemperature = 1/temperature.value
    attenuationCoefficient = 0.99
    internalFactors = [[inverseTemperature , 0.001],[energyGain,0.000001]]
    externalFactors = [["Damaged infrastructures",0, 0.001],["Energy tax", 0, 0.001]]
    HOST = "localhost"
    PORT = 1791
    
    weather = Process(target=weatherFunction, args=(lockTemperature,))
    weather.start()
    transaction = threading.Thread(target=transactionHandler, args = (lockPrice_wrt, lockPrice_read, lockGain,))
    transaction.start()
    priceCalculator = threading.Thread(target = priceCalculatorFunction, args = (attenuationCoefficient, internalFactors, externalFactors, lockPrice_wrt, lockTemperature, lockExternal, lockGain))
    priceCalculator.start()
    external = Process(target=externalFunction, args=())
    external.start()
    transaction.join()
    external.join()
    weather.join()
    priceCalculator.join()