# Reads Galaxy editor upgrade_messages for each imported workflow (read-only API calls).
import json,sys,time,urllib.request
base=sys.argv[1]; out=sys.argv[2]
def get(path,key,method='GET'):
    r=urllib.request.Request(base+path,method=method,headers={'x-api-key':key}); return json.load(urllib.request.urlopen(r))
admin='test_key'
deadline=time.time()+3000
while True:
    try:
        users=[u for u in get('/api/users',admin) if u['email']=='planemo@galaxyproject.org']
        if users:
            ukey=get(f"/api/users/{users[0]['id']}/api_key/detailed",admin).get('key')
            wfs=get('/api/workflows',ukey)
            if len(wfs)>=2: break
    except Exception as e: pass
    if time.time()>deadline: sys.exit('timeout waiting for workflows')
    time.sleep(15)
time.sleep(5)
res={}
for w in get('/api/workflows',ukey):
    ed=get(f"/api/workflows/{w['id']}/download?style=editor",ukey)
    labels={str(k):s.get('label') for k,s in ed['steps'].items()}
    msgs={labels.get(str(k),k):v for k,v in ed['upgrade_messages'].items()}
    res[w['id']+' | update_time '+str(w.get('update_time'))]=msgs
json.dump(res,open(out,'w'),indent=1)
print('done')
