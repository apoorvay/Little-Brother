# Little-Brother
A Remote Host Monitoring System
MONITOR RPI (CLIENT)

Initialization: Run from command line using: python3 pistatsview.py </br>
Command line arguments (to establish a connection to the message broker) </br>
-b message broker (IP address or named address of the message broker to connect to) </br>
-p virtual host (optional) (default: '/') (Virtual host to connect to on the message broker) </br>
-c login:password (optional) (default: 'guest:guest') (Credentials to connect to the message broker) </br>
-k routing key (To use for filtering when subscribed to the pi_utilization exchange on the message broker) </br>

Libraries Used: </br>
pika:		To establish a connection to the message broker </br>
json:		To unparse the json message received over the message queue </br>
argparse: 	To parse the command line arguments </br>
sys:		To handle connection exceptions </br>

HOST RPI (SERVER) </br>

MONITOR RPI (CLIENT) </br>

Initialization: Run from command line using: python3 pistatsd.py </br>
Command line arguments (to establish a connection to the message broker) </br>
-b message broker (IP address or named address of the message broker to connect to) </br>
-p virtual host (optional) (default: '/') (Virtual host to connect to on the message broker) </br>
-c login:password (optional) (default: 'guest:guest') (Credentials to connect to the message broker) </br>
-k routing key (To use for filtering when subscribed to the pi_utilization exchange on the message broker) </br>

Libraries Used: </br>
pika:		To establish a connection to the message broker </br>
json:		To unparse the json message received over the message queue </br>
argparse: 	To parse the command line arguments </br>
sys:		To handle connection exceptions </br>
sleep:		To read CPU and network utilization information every second </br>
pika.exceptions:To raise connection exceptions </br>
