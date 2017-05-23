#!/usr/bin/env python
import pika
import json
from time import sleep
import sys, getopt, argparse
#from StringIO import StringIO
import re
import time
from pika.exceptions import (ConnectionClosed, AMQPConnectionError, AMQPChannelError)

#Parse arguments (optional and required)
parser = argparse.ArgumentParser()

parser.add_argument('-b', required=True, dest="broker")
parser.add_argument('-p', default = '/', dest="vhost")
parser.add_argument('-c', default = 'guest:guest', dest="usercred")
parser.add_argument('-k', required=True, dest="routkey")

#Use parsed argument to obtain user credentials
arguments = parser.parse_args()
[user,passwd] = arguments.usercred.split(":")

#Try to establish a connection using specified parameters
credentials = pika.PlainCredentials(user,passwd)
parameters = pika.ConnectionParameters(arguments.broker ,5672, arguments.vhost ,credentials)
try:
    connection = pika.BlockingConnection(parameters)
except :
    print("Failed to establish a blocking connection. Please try again.")
    sys.exit(1)
channel = connection.channel()

#Establish a connection using the routing key specified
channel.queue_declare(queue = arguments.routkey)

regexp = r"""
  \s*                     # a interface line  starts with none, one or more whitespaces
  (?P<interface>\w+):\s+  # the name of the interface followed by a colon and spaces
  (?P<rx_bytes>\d+)\s+    # the number of received bytes and one or more whitespaces
  (?P<rx_packets>\d+)\s+  # the number of received packets and one or more whitespaces
  (?P<rx_errors>\d+)\s+   # the number of receive errors and one or more whitespaces
  (?P<rx_drop>\d+)\s+      # the number of dropped rx packets and ...
  (?P<rx_fifo>\d+)\s+      # rx fifo
  (?P<rx_frame>\d+)\s+     # rx frame
  (?P<rx_compr>\d+)\s+     # rx compressed
  (?P<rx_multicast>\d+)\s+ # rx multicast
  (?P<tx_bytes>\d+)\s+    # the number of transmitted bytes and one or more whitespaces
  (?P<tx_packets>\d+)\s+  # the number of transmitted packets and one or more whitespaces
  (?P<tx_errors>\d+)\s+   # the number of transmit errors and one or more whitespaces
  (?P<tx_drop>\d+)\s+      # the number of dropped tx packets and ...
  (?P<tx_fifo>\d+)\s+      # tx fifo
  (?P<tx_frame>\d+)\s+     # tx frame
  (?P<tx_compr>\d+)\s+     # tx compressed
  (?P<tx_multicast>\d+)\s* # tx multicast
"""


pattern = re.compile(regexp, re.VERBOSE)

#Initialize CPU utilization values
last_idle = last_total = 0

#Compute CPU Utilization values
def getStat():

    global last_idle, last_total
    with open('/proc/stat') as f:
        fields = [float(column) for column in f.readline().strip().split()[1:]]
    idle, total = fields[3], sum(fields)
    idle_delta, total_delta = idle - last_idle, total - last_total
    last_idle, last_total = idle, total
    utilisation = (1.0 - idle_delta / total_delta)
    f.close()
#   print(str(utilisation))
    return (str(utilisation))



def get_bytes(interface_name):
    '''returns tuple of (rx_bytes, tx_bytes) '''
    with open('/proc/net/dev', 'r') as f:
        a = f.readline()
        while(a):
            m = pattern.search(a)
            # the regexp matched
            # look for the needed interface and return the rx_bytes and tx_bytes
            if m:
                if m.group('interface') == interface_name:
                    return (m.group('rx_bytes'),m.group('tx_bytes'))
            a = f.readline()

def calculateThroughput(interface, last_bytes):
    
    now_bytes = get_bytes(interface)
   
    rx = int(now_bytes[0]) - int(last_bytes[0])
    tx = int(now_bytes[1]) - int(last_bytes[1])
    return (rx, tx)

while (1):

    #Computer previous network values
    last_time  = time.time()
    last_bytes_lo = get_bytes("lo")
    last_bytes_wlan0 = get_bytes("wlan0")
    last_bytes_eth0 = get_bytes("eth0")

    #Time period of obtaining CPU and network throughput
    time.sleep(1)
    
    bytes_lo = calculateThroughput("lo",last_bytes_lo)
    rx_lo = bytes_lo[0]
    tx_lo = bytes_lo[1]
    
    bytes_wlan = calculateThroughput("wlan0",last_bytes_wlan0)
    rx_wlan = bytes_wlan[0]
    tx_wlan = bytes_wlan[1]

    bytes_eth = calculateThroughput("eth0",last_bytes_eth0)
    rx_eth = bytes_eth[0]
    tx_eth = bytes_eth[1]
 
    print "rx: %s B/s, tx %s B/s" % (rx_wlan, tx_wlan)

    #Parse JSON message to publish to message queue
    message = json.dumps({"net": {
                            "lo": {
                                "rx":rx_lo,
                                "tx":tx_lo
                                },
                            "wlan0": {
                                "rx": rx_wlan,
                                "tx": tx_wlan
                                },
                            "eth0": {
                                "rx": rx_eth,
                                "tx": tx_eth
                                }
                            },
                      "cpu" : getStat()
                      })

    #Bind and publish message to direct exchange using routing key
    channel.queue_bind(exchange="pi_utilization",queue=arguments.routkey, routing_key = arguments.routkey)
    channel.basic_publish(exchange='pi_utilization', routing_key = arguments.routkey, body = message)

 #   print(message)

connection.close()

