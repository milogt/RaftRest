TESTING INSTRUCTION:
I have created a python script client_test.py, which takes arguments to execute a request. To run the
test script, use command following the format below:
python3 client_test.py <port> <request type> <topic> <message> (topic and message is optional)

You can use 5 types of request as below:
addtopic, gettopic, addmsg, getmsg, getstate

1. MESSAGE QUEUE
To test the correctness of my message queue, I use client_test.py to make different test request, and
let the server prints out storing messages and log. I ran three servers on different ports, and send
request to the leader server. If the topic with addtopic request doesn't exist, I will receive a 
false success response with error number 400. Same thing for addmsg to a topic that hasn't been 
created, I received a negative response. When I use gettopic and getmsg, client_test.py will print 
out the topic list or message from a specific topic. Test request getstate will also print out the 
response such as leader and follow. This approves that my message queue implementation is correct.

2. ELECTION ALGORITHM
In my server.py, I let server prints out the process log during election. I opened two terminals and 
ran two servers on different ports. These two servers will keep starting new election since there are 
only two in the cluster. Either one of them cannot become the leader node since they cannot receive 
more than half vote, which is correct.

Then I start another server, which makes the cluster in size three. One of them will become the 
leader with a message print out. Then the followers will start receiving heartbeat continually shown 
in terminal. Then I start the fourth server and kill the leader node, one of the rest will start a 
new election process and become the leader. 

3. DISTRIBUTED REPLICATION
To test the correctness of my replication model, I let the server print out the messages stored in 
each node after committing a new request. I tried using multiple types of requests such as add new 
topic, add new message, and get a message from a topic. Then I compare the printout results of each 
server and make sure that messages keep consistent. Then I killed the leader server and sent request 
to the new leader to get the topic list and message. It turned out the response returned is what I 
expected. Since the messages are proved to be consistent, it means requests are committed following 
the same order in every server. It also proves that every log eventually contains the same requests 
in the same order.




