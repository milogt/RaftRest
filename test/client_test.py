import sys
import requests

if __name__ == '__main__':
    port = sys.argv[1]
    func = sys.argv[2]
    if len(sys.argv) > 3:
        topic = sys.argv[3]
    if len(sys.argv) > 4:
        message = sys.argv[4]

    if func == "addtopic":
        data = {'topic': topic}
        res = requests.put("http://127.0.0.1:"+port+"/topic", json=data)
        print(res.json())
    elif func == "gettopic":
        res = requests.get("http://127.0.0.1:"+port+"/topic")
        print(res.json())
    elif func == "addmsg":
        data = {'topic':topic, 'message':message}
        res = requests.put("http://127.0.0.1:"+port+"/message", json=data)
        print(res.json())
    elif func == "getmsg":
        res = requests.get("http://127.0.0.1:"+port+"/message/"+topic)
        print(res.json())
    elif func == "getstate":
        res = requests.get("http://127.0.0.1:"+port+"/status")
        print(res.json())
    else:
        print("wrong command")
