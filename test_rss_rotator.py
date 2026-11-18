import requests
import time
import xml.etree.ElementTree as ET

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1'
]

subs = ['forhire', 'freelance_forhire', 'smallbusiness', 'Entrepreneur', 'webdev', 'startups', 'HiringCoding']

for i, sub in enumerate(subs):
    ua = user_agents[i % len(user_agents)]
    headers = {'User-Agent': ua}
    time.sleep(2.5)
    r = requests.get(f'https://www.reddit.com/r/{sub}/new/.rss', headers=headers, timeout=8)
    print(f"r/{sub} status with UA {i}: {r.status_code}")
    if r.status_code == 200:
        root = ET.fromstring(r.text)
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        print(f"  -> Got {len(entries)} posts!")
