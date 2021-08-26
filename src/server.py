from threading import Thread, Lock
import time
import random
import requests

Process = Thread

def communicate(ip, func, content):
    try:
        response = requests.post(url=ip+'/'+func,json=content,timeout=0.05,)
        if response.status_code == 200:
            return response
    except Exception as e:
        return None
    return None

class Server():
    def __init__(self, server_list, index):
        print("server initialized.")
        self.ip = server_list.pop(index)
        self.cluster = server_list
        self.messages = {}
        self.timeout = 0
        self.check_loop = None
        self.lock = Lock()
        self.state = 'Follower'
        self.vote = 0
        self.leader = None
        self.term = 0
        self.log = []
        self.commitIdx = 0
        self.entry = None
        self.init_time()

    def handle_client(self, request):
        self.lock.acquire()
        self.entry = request
        wait_time = 0
        log = {'ip':self.ip, 'term':self.term, 'log':request, 'request': 'log', 'commitIdx':self.commitIdx}
        check_list = len(self.cluster)*[0]
        p = Process(target=self.distribute_data, args=(log, check_list, None,))
        p.start()
        while sum(check_list) < (len(self.cluster)+1)//2:
            wait_time += 0.001
            time.sleep(0.001)
            if wait_time > 0.1:
                self.lock.release()
                return False
        log['request'] = 'commit'
        self.commit()
        p = Process(target=self.distribute_data, args=(log, None, self.lock,))
        p.start()
        return True


    def distribute_data(self, data, check_list, lock):
        index = 0
        for i in self.cluster:
            response = communicate(i, 'heartbeat', data)
            if data['request'] == 'log' and response != None:
                check_list[index] = 1
            index += 1
        if data['request'] == 'commit' and lock:
            lock.release()


    def reset_time(self):
        self.timeout = random.uniform(0.2,0.4)+time.time()

    def checking(self):
        while self.state != 'Leader':
            if time.time() >= self.timeout:
                self.election()
            else:
                time.sleep(0.2)

    def init_time(self):
        self.reset_time()
        if self.check_loop and self.check_loop.isAlive():
            return
        else:
            self.check_loop = Process(target=self.checking)
            self.check_loop.start()

    def election(self):
        print("start election")
        self.state = 'Candidate'
        self.term += 1
        self.vote = 0
        self.init_time()
        self.calculate_vote()
        for i in self.cluster:
            p = Process(target=self.collect_vote, args=(i,self.term))
            p.start()

    def collect_vote(self, server, term):
        while self.state == 'Candidate' and self.term == term:
            content = {'term':term, 'commitIdx':self.commitIdx,'entry':self.entry}
            response = communicate(server, "vote", content)
            if response != None:
                vote = response.json()['vote']
                if vote == True and self.state == 'Candidate':
                    self.calculate_vote()
                else:
                    term = response.json()['term']
                    if term > self.term:
                        self.term = term
                        self.state = 'Follower'
                return
            time.sleep(0.001)

    def calculate_vote(self):
        self.vote += 1
        if self.vote >= (len(self.cluster)+1)//2+1:
            self.state = 'Leader'
            print(self.ip + " becomes leader.")
            if self.entry:
                self.handle_client(self.entry)
            for i in self.cluster:
                p = Process(target=self.send_heartbeat, args=(i,))
                p.start()

    def send_vote(self, term, lastLogIndex, lastLog):
        if term > self.term and lastLogIndex >= self.commitIdx:
            if lastLog or lastLog == self.entry:
                self.reset_time()
                self.term = term
                return True, self.term
        return False, self.term

    def check_commit_index(self, receiver):
        content = {'ip':self.ip, 'term':self.term}
        response = communicate(receiver, 'heartbeat', content)
        if response != None:
            if self.commitIdx > response.json()['commitIdx']:
                content = {'ip':self.ip, 'term':self.term, 'request':'commit','log':self.log[-1]}
                response = communicate(receiver, 'heartbeat', content)

    def check_term(self, term, commitIdx):
        if self.term < term:
            self.term = term
            self.state = 'Follower'
            self.init_time()

    def send_heartbeat(self, receiver):
        if self.log:
            self.check_commit_index(receiver)
        content = {'ip':self.ip, 'term':self.term}
        while self.state == 'Leader':
            # print("send heartbeat.")
            cur_time = time.time()
            response = communicate(receiver, 'heartbeat', content)
            if response != None:
                msg = response.json()
                self.check_term(msg['term'],msg['commitIdx'])
            time.sleep((50-(time.time()-cur_time))/1000)

    def receive_heartbeat(self, content):
        if self.term <= content['term']:
            self.term = content['term']
            self.leader = content['ip']
            self.reset_time()
            if self.state == 'Candidate':
                self.state = 'Follower'
            elif self.state == 'Leader':
                self.state = 'Follower'
                self.init_time()
            if 'request' in content:
                if content['request'] == 'log':
                    self.entry = content['log']
                elif content['commitIdx'] >= self.commitIdx:
                    if not self.entry:
                        self.entry = content['log']
                    self.commit()
        return {'term':self.term, 'commitIdx':self.commitIdx}

    def commit(self):
        self.commitIdx += 1
        self.log.append(self.entry)
        topic = self.entry['topic']
        if self.entry['type'] == 'addTopic':
            self.messages[topic] = []
        elif self.entry['type'] == 'addMessage':
            msg = self.entry['message']
            self.messages[topic].append(msg)
        elif self.entry['type'] == 'getMessage':
            msg = self.messages[topic].pop(0)
        self.entry = None
        # print(self.message)
