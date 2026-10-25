"""Process-only DNS fallback; the service hostname, SNI and TLS checks stay intact.

Addresses must come from the host OS resolution of the configured service name.
Never change request URLs, authentication, certificate checking or search code.
"""
import ipaddress
import json
import os
import runpy
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

root=Path(__file__).resolve().parent
data=json.loads((root/'transport_dns.json').read_text(encoding='utf-8-sig'))
host=urlparse(os.environ['LLM_BASE_URL']).hostname
assert data['host']==host
addresses=data['addresses']
assert addresses and all(ipaddress.ip_address(a).is_global for a in addresses)
assert time.time()-data['resolved_unix']<3600, 'Refresh host DNS before launching'
original=socket.getaddrinfo


def record(value):
    with (root/'transport_events.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(dict(time_unix=time.time(),**value))+'\n')


def resolve(name,port,*args,**kwargs):
    try:
        return original(name,port,*args,**kwargs)
    except socket.gaierror as exc:
        actual=name.decode() if isinstance(name,bytes) else name
        if actual!=host: raise
        result=[]
        for address in addresses:
            result.extend(original(address,port,*args,**kwargs))
        record(dict(event='dns_fallback',hostname=host,addresses=addresses,error=str(exc)))
        return result


socket.getaddrinfo=resolve
record(dict(event='launch',hostname=host,addresses=addresses,resolved_unix=data['resolved_unix'],
            request_hostname_unchanged=True,tls_verification_unchanged=True))
target=sys.argv[1]
assert target in {'experiment.py','check_support.py'}
sys.argv=[str(root/target),*sys.argv[2:]]
runpy.run_path(str(root/target),run_name='__main__')
