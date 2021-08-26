1. MESSAGE QUEUE	
To implement the single server message-queue, I used FLASK to create multiple functions for clients 
to communicate with the server. In node.py, I used route decorator "topic" to bind a get and a put
function to handle client's request to create a topic and get a list of existing topics. If the 
topic name is already created or the receiving server is not a leader, client will receive a response
with false success. Otherwise, the request will be passed to the leader server to process. A get
topics request will only be processed if the server is the lead server. Since we don't need to log
the get request, it will simply return the list of topic names without informing other servers.

I also implement a route decorator "message" to handle a message get/put request. The message will
be passed as json format with name "topic" and "message" when client wants to add a new message. If
the topic name doesn't exist or receiving server is not a leader, a false success response will be
returned to the client. Otherwise, the request will be passed to leader with function handle_client
to log and commit. To get a message in a specific topic, which is included in the URL as a variable, 
the request also needs to be logged and committed to other servers in the cluster. If the message
queue in this topic is empty, a false success response will be returned.

2. ELECTION ALGORITHMS
To implement the election procedure, I create a class called Server, which has variables cluster(the
list of ip addresses of other servers in the same cluster), timeout(the expiring time of election to
ensure a leader in the cluster or restart election), state(current state of a server), term(the index
of each election round), and vote(the number of votes of the server in each election).

When a server starts to run, I let it initiates a timeout period. If it doesn't receive a heartbeat
or update its timeout, which means there is no leader within this cluster, it starts an election. I 
defined a method "election", which changes the server's state to candidate and increment the term by 
1. Then it sends vote requests to all the other servers by initiating multiple threads with function
collect_vote. Meanwhile, the candidate server will keep calculating until it receives more than half 
votes. Collect_vote is sent by function "communicate", which sends request to other servers asking
for vote decisions. Within the request, I decide to include term, last log index, and last log, to 
ensure the candidate is in the newest term and receive client request if an entry is created before 
a leader is elected. 

When a follower server receives a vote request, it will first check if its own term is behind the
candidate's term, and its commit index is behind or in the same one with the candidate's. Then it
makes a decision based on the last log sent by candidate. If there is a new log, or they have the
same last log, which means the log is up-to-date, it will return True and then reset its timeout. 
Otherwise, it send a vote with response false. 

The "calculate_vote" will increment its own vote and check if the candidate receives more than half
votes. I decide to calculate the vote every time it receives a vote instead of using a while loop to
keep counting the vote, which is way more expensive. If it doesn't receive enough votes after
timeout, it returns to follower state and starts a new election. Function "collect_vote" ensures that
if it receives a false response with a higher term, which means a new leader is elected already, the
candidate becomes follower and update to the new term. Once it receives enough votes, it changes the
state to leader and send heartbeat to other servers. If a new request is already been created by
client, it handles the request immediately.

In each heartbeat, it sends the leader's term to followers. Followers will send back a message with
its own term. If the term is higher than the leader's term, which means there is a new leader within
the cluster, it returns to follower state and reset its timeout. For a follower, I created a method
"receive_heartbeat" to ensure it follows the current election term if it hasn't received the new 
leader's vote request. If a leader or candidate receives a heartbeat, it becomes a follower again.

3. DISTRIBUTED REPLICATION 
To implement the state machine for each server, I created a private variable, log, for class Server.
Variable entry updates when receiving new request from client in function "handle_client". We first
lock the thread to make sure we only handle one request every time to avoid a race condition. 

Then I create a log message including term, request content, and commit index, to ensure log 
consistency and each server is in the same state. Function "distribute_data" will send the log 
message to each server in the cluster and update its entry. If server x has updated successfully, it 
will mark the check list true at index x. After receiving more than half replies, it will resent the 
log message to let the other servers commit the new entry. After self commitment, lead server return
response to client and unlock the lock to handle following requests.

In method "commit", I decide to pass a request type based on client's request type. So the commit
can easily handle different types of requests according to the attribute value. In commit procedure,
we first increment the commit index and then set the entry value back to None since it's already 
logged into the state machine.

To prevent a server crash before committing the request, I also include a check_commit_index process 
before sending a heartbeat. It checks every follower server's commit index when a new leader claims 
the position. If follower's commit index is smaller than the leader's, it sends its last log and asks
the follower to commit the request to keep the model consistent.


POSSIBLE SHORTCOMMINGS:
In my implementation of distributed replication, I choose to set a timeout to receive update 
confirmation, that returns false to client if the leader doesn't receive more than half replies. At 
this point, it might be the situation that multiple follower servers crashed. If we keep trying 
sending log message until receiving majority positive response, the system would get stuck in a 
deadlock since crashed servers haven't come back to life. In my case, we can easily detect the issue 
and start to debug our server system. However, we could possibly lose client's request or client's 
needs to retry submitting request until receiving success response.

Besides that, I wonder if the leader server crashed before committing the new request. Since other 
servers have received the latest log and will commit it when the new leader is elected. But we still 
may have an issue that client hasn't received success response but the request is committed. If the 
client is unaware of the situation, he could possibly retry sending the same request, which makes 
redundant data and lead to undesirable results. 

ONLINE REFERENCE SOURCE:
https://www.youtube.com/watch?v=RHDP_KCrjUc
https://www.geeksforgeeks.org/raft-consensus-algorithm/
https://github.com/streed/simpleRaft
https://github.com/goraft/raft
https://github.com/Oaklight/Vesper
https://github.com/kurin/py-raft


