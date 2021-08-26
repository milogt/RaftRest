from flask import Flask,request
import sys
import json
from server import Server

app = Flask(__name__)


@app.route("/topic", methods=['PUT'])
def create_topic():
    topic = request.json['topic']
    if topic in s.messages.keys() or s.state != 'Leader':
        return {"success":False}, 400
    response = s.handle_client({'type':'addTopic','topic':topic})
    if response:
        # print(topics)
        return {"success":True}, 200
    return {"success":False}, 400

@app.route('/topic', methods=['GET'])
def get_topics():
    if s.state != 'Leader':
        return {'success':False, 'topics':[]}, 200
    names = list(s.messages.keys())
    return {'success':True, 'topics':names}, 200

@app.route('/message', methods=['PUT'])
def add_message():
    topic = request.json['topic']
    msg = request.json['message']
    if topic not in s.messages.keys() or s.state != 'Leader':
        return {"success":False}, 400
    response = s.handle_client({'type':'addMessage','topic':topic,'message':msg})
    if response:
        return {'success':True}, 200
    return {'success':False}, 400

@app.route('/message/<topic>', methods=['GET'])
def get_message(topic):
    if topic not in s.messages.keys() or s.state != 'Leader':
        return {'success':False}
    if len(s.messages[topic]) > 0:
        msg = s.messages[topic][0]
        response = s.handle_client({'type':'getMessage','topic':topic})
        if response:
            return {'success':True, 'message':msg}
    return {'success':False}

@app.route('/status', methods=['GET'])
def get_status():
    return {'role':s.state, 'term':s.term}

@app.route("/vote", methods=['POST'])
def vote():
    term = request.json["term"]
    commitIdx = request.json["commitIdx"]
    entry = request.json["entry"]
    vote, term = s.send_vote(term, commitIdx, entry)
    return {"vote": vote, "term": term}

@app.route("/heartbeat", methods=['POST'])
def heartbeat():
    response = s.receive_heartbeat(request.json)
    return response



if __name__ == '__main__':
    file = sys.argv[1]
    index = int(sys.argv[2])
    with open(file) as f:
        data = json.load(f)

    ports_list = []
    for i in data['addresses']:
        ports_list.append(i['ip']+':'+str(i['port']))
    cur_port = data['addresses'][index]['port']

    s = Server(ports_list, index)
    app.run(port=cur_port, debug=False)
