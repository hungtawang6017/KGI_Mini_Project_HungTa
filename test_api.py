import urllib.request
import json

data = json.dumps({'agent_id':'tester_01', 'event_type':'course_completion', 'is_quiz_perfect':False}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/api/learning/complete-session', data=data, headers={'Content-Type':'application/json'})

try:
    res = urllib.request.urlopen(req)
    print(res.read())
except Exception as e:
    print(e.read().decode())
