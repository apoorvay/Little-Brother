import pika
import json
from pymongo import MongoClient
import sys, argparse
import RPi.GPIO as GPIO


# command line arguments parsing
parser = argparse.ArgumentParser()
parser.add_argument('-b', required=True, dest="broker")
parser.add_argument('-p', default = '/', dest="vhost")
parser.add_argument('-c', default = 'guest:guest', dest="usercred")
parser.add_argument('-k', required=True, dest="routkey")

arguments = parser.parse_args()
[user,passwd] = arguments.usercred.split(":")

credentials = pika.PlainCredentials(user,passwd)
parameters = pika.ConnectionParameters(arguments.broker ,5672, arguments.vhost ,credentials)

# try to have a blocking connection
try:
    connection = pika.BlockingConnection(parameters)
except :
    print("Failed to establish a blocking connection. Please try again.")
    sys.exit(1)
    
channel = connection.channel()

channel.queue_declare(queue = arguments.routkey)

# connect to database
try:
    client = MongoClient()
    db = client.bigBrother
except pymongo.errors.ConnectionFailure, e:
    print "Could not connect to server %s" %e
    sys.exit(1)


# update the led based on the cpu threshold value
def updateLED(threshold):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(29, GPIO.OUT) #RED
        GPIO.setup(31, GPIO.OUT) #GREEN
        GPIO.setup(33,GPIO.OUT) #BLUE
        # green
        if(threshold < 0.25):
            GPIO.output(29, False)
            GPIO.output(31, True)
            GPIO.output(33, False)
        #yellow
        elif(threshold < 0.5):
            GPIO.output(29, True)
            GPIO.output(31, True)
            GPIO.output(33, False)
        #red
        elif(threshold > 0.5):
            GPIO.output(29, True)
            GPIO.output(31, False)
            GPIO.output(33, False)

 # find max value           
def findHigh(query):
    try:
        a = db.test_bigBrother.find().sort([(query, -1)]).limit(1) #max
        return a
    except pymongo.errors.ExecutionTimeout, e:
        print "Database operation timed out %s" %e
        sys.exit(1)    

# find min value
def findLow(query):
    try:
        a = db.test_bigBrother.find().sort([(query, 1)]).limit(1) #min
        return a
    except pymongo.errors.ExecutionTimeout, e:
        print "Database operation timed out %s" %e
        sys.exit(1)    

# print to terminal
def printOut(messageJson):
    hi_cpu = 0
    low_cpu = 0
    high_rx_lo = 0
    low_rx_lo = 0
    high_tx_lo = 0
    low_tx_lo =0
    high_rx_eth = 0
    low_rx_eth = 0
    high_tx_eth = 0
    low_tx_eth =0
    high_rx_wlan = 0
    low_rx_wlan = 0
    high_tx_wlan = 0
    low_tx_wlan = 0

    
    cpuH = findHigh('cpu')
    for a in cpuH:
        hi_cpu = a['cpu']

    cpuL = findLow('cpu')
    for a in cpuL:
        low_cpu = a['cpu']

    lo_rx_h = findHigh('net.lo.rx')
    for a in lo_rx_h:
        high_rx_lo = a['net']['lo']['rx']


    lo_rx_l = findLow('net.lo.rx')
    for a in lo_rx_l:
        low_rx_lo = a['net']['lo']['rx']


    lo_tx_h = findHigh('net.lo.tx')
    for a in lo_tx_h:
        high_tx_lo = a['net']['lo']['tx']


    lo_tx_l = findLow('net.lo.tx')
    for a in lo_tx_l:
        low_tx_lo = a['net']['lo']['tx']


    eth_rx_h = findHigh('net.eth0.rx')
    for a in eth_rx_h:
        high_rx_eth = a['net']['eth0']['rx']


    eth_rx_l = findLow('net.eth0.rx')
    for a in eth_rx_l:
        low_rx_eth = a['net']['eth0']['rx']


    eth_tx_h = findHigh('net.eth0.tx')
    for a in eth_tx_h:
        high_tx_eth = a['net']['eth0']['tx']


    eth_tx_l = findLow('net.eth0.tx')
    for a in eth_tx_l:
        low_tx_eth = a['net']['eth0']['tx']




    wlan_rx_h = findHigh('net.wlan0.rx')
    for a in wlan_rx_h:
        high_rx_wlan = a['net']['wlan0']['rx']


    wlan_rx_l = findLow('net.wlan0.rx')
    for a in wlan_rx_l:
        low_rx_wlan = a['net']['wlan0']['rx']


    wlan_tx_h = findHigh('net.wlan0.tx')
    for a in wlan_tx_h:
        high_tx_wlan = a['net']['wlan0']['tx']


    wlan_tx_l = findLow('net.wlan0.tx')
    for a in wlan_tx_l:
        low_tx_wlan = a['net']['wlan0']['tx']

        

    print (arguments.routkey)
    print ('cpu: ' +  messageJson['cpu'] + ' [Hi: ' +  str(hi_cpu) + ', Lo: ' + str(low_cpu) + ']')

    print ('lo: rx=' +  str(messageJson['net']['lo']['rx']) + ' B/s' + ' [Hi: ' + 
    str(high_rx_lo) + 'B/s, Lo: ' + str(low_rx_lo) + 'B/s], tx= ' + str(messageJson['net']['lo']['tx']) + 'B/s [Hi: ' + str(high_tx_lo) + 'B/s, Lo: ' + str(low_tx_lo) + 'B/s]')

    print ('eth0: rx=' +  str(messageJson['net']['eth0']['rx']) + ' B/s' + ' [Hi: ' + str(high_rx_eth) + 'B/s , Low: ' + str(low_rx_eth) + 'B/s], tx= ' + str(messageJson['net']['eth0']['tx']) + 'B/s [Hi: ' + str(high_tx_eth) + 'B/s, Lo: ' + str(low_tx_eth) + 'B/s]')


    print ('wlan0: rx=' +  str(messageJson['net']['wlan0']['rx']) + ' B/s' + ' [Hi: ' +  str(high_rx_wlan) + 'B/s , Low: ' + str(low_rx_wlan) + 'B/s], tx= ' + str(messageJson['net']['wlan0']['tx']) + 'B/s [Hi: ' + str(high_tx_wlan) + 'B/s, Lo: ' + str(low_tx_wlan) + 'B/s]')

    print ('\n')

    
def callback(ch, method, properties, body):
    messageReceived = ("%r" %body).strip('b').strip("'")
    messageJson = json.loads(messageReceived)
    printOut (messageJson) # prints to stdout
    updateLED(float(messageJson['cpu'])) # update the leds

    # insert to database
    try:
        result = db.test_bigBrother.insert_one(messageJson)    
    except pymongo.errors.ExecutionTimeout, e:
        print "Database operation timed out %s" %e
        sys.exit(1)    


    post_id = result.inserted_id
    

channel.queue_bind(exchange="pi_utilization",queue=arguments.routkey, routing_key = arguments.routkey)
channel.basic_consume(callback, queue = arguments.routkey, no_ack=True)


print(' [*] Waiting for messages. To exit press Ctrl+C')
channel.start_consuming()

