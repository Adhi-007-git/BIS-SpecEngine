import urllib.request
import urllib.parse
import json

f = urllib.request.urlopen('http://localhost:8000/api/standards')
standards = json.loads(f.read().decode('utf-8'))
print(f"Total catalogue standards: {len(standards)}")

for s in standards:
    num = s['standard_number']
    url = f"http://localhost:8000/api/graph/{urllib.parse.quote(num)}"
    try:
        res = urllib.request.urlopen(url)
        data = json.loads(res.read().decode('utf-8'))
        nodes = data.get("total_nodes", 0)
        edges = data.get("total_edges", 0)
        print(f"{num:25} | nodes={nodes} | edges={edges} | title={s.get('title')[:40]}")
    except Exception as e:
        print(f"{num:25} | ERROR: {e}")
