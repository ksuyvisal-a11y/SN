import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
import server

client = server.app.test_client()
r = client.get('/api/downloader/drama/hg_7679018384272395289')
data = r.get_json()
print("Success:", data.get("success"))
drama = data.get("drama")
print("Drama:", drama.get("title"), "id:", drama.get("id"))
eps = data.get("episodes", [])
print("Episodes count:", len(eps))
for i in range(min(5, len(eps))):
    e = eps[i]
    print(f"  EP {e.get('episode_num')}: stream_url={e.get('stream_url')}, download_url={e.get('download_url')}, source={e.get('source')}, vid={e.get('vid')}")
