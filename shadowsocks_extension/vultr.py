from asynctools.servers import Connection
import requests
from termcolor import cprint,colored
import json
import os
import re
import cmd
import getpass
import base64
from seed.mrpackage.config import Host, Cache, DB_PATH

INIT_PAYLOAD = b"""IyEvYmluL2Jhc2gKI2luc3RhbGwgcHl0aG9uCgpoYXNoIGFwdCAyPi9kZXYvbnVsbAppZiBbICQ/IC1lcSAwIF07dGhlbgogICAgZWNobyAiYXB0IGlzIGV4aXN0ZWQgaW5zdGFsbCBhcHQtbGliIgogICAgYXB0LWdldCBpbnN0YWxsIC15IGxpYmM2LWRldiBnY2MKICAgIGFwdC1nZXQgaW5zdGFsbCAteSBtYWtlIGJ1aWxkLWVzc2VudGlhbCBsaWJzc2wtZGV2IHpsaWIxZy1kZXYgbGlicmVhZGxpbmUtZGV2IGxpYnNxbGl0ZTMtZGV2IHdnZXQgY3VybCBsbHZtCmVsc2UKICAgIGhhc2ggeXVtIDI+L2Rldi9udWxsCiAgICBpZiBbICQ/IC1lcSAwIF07dGhlbgogICAgICAgIGVjaG8gInl1bSBpcyBleGlzdGVkIGluc3RhbGwgeXVtLWxpYiIKICAgICAgICB5dW0gLXkgaW5zdGFsbCB3Z2V0IGdjYyBtYWtlIGVwZWwtcmVsZWFzZQogICAgICAgIHl1bSB1cGRhdGUgLXkKICAgICAgICB5dW0gLXkgaW5zdGFsbCAgbmV0LXRvb2xzCiAgICAgICAgeXVtIC15IGluc3RhbGwgemxpYjFnLWRldiBiemlwMi1kZXZlbCBvcGVuc3NsLWRldmVsIG5jdXJzZXMtZGV2ZWwgc3FsaXRlLWRldmVsIHJlYWRsaW5lLWRldmVsIHRrLWRldmVsIGdkYm0tZGV2ZWwgZGI0LWRldmVsIGxpYnBjYXAtZGV2ZWwgeHotZGV2ZWwKICAgIGZpCmZpCgoKaGFzaCBweXRob24zIDI+L2Rldi9udWxsCiAgICBpZiAgWyAkPyAtZXEgMCBdO3RoZW4KICAgIHJlcz0kKHB5dGhvbjMgLVYgMj4mMSB8IGF3ayAne3ByaW50ICQxfScpCiAgICB2ZXJzaW9uPSQocHl0aG9uMyAtViAyPiYxIHwgYXdrICd7cHJpbnQgJDJ9JykKICAgICNlY2hvICJjaGVjayBjb21tYW5kKHB5dGhvbikgYXZhaWxhYmxlIHJlc3V0bHMgYXJlOiAkcmVzIgogICAgaWYgWyAiJHJlcyIgPT0gIlB5dGhvbiIgXTt0aGVuCiAgICAgICAgaWYgICBbICIke3ZlcnNpb246MDozfSIgPT0gIjMuNiIgXTt0aGVuCiAgICAgICAgICAgIGVjaG8gIkNvbW1hbmQgcHl0aG9uMyBjb3VsZCBiZSB1c2VkIGFscmVhZHkuIgogICAgICAgICAgICAgICAgIGhhc2ggcGlwMyAyPi9kZXYvbnVsbDsKICAgICAgICAgICAgICAgICBpZiBbICQ/IC1lcSAgMCBdO3RoZW4KICAgICAgICAgICAgICAgICAgICBwaXAzIGluc3RhbGwgLVUgZ2l0K2h0dHBzOi8vZ2l0aHViLmNvbS9zaGFkb3dzb2Nrcy9zaGFkb3dzb2Nrcy5naXRAbWFzdGVyCiAgICAgICAgICAgICAgICAgICAgcGlwMyBpbnN0YWxsIHgtbXJveS0xMDQ1CiAgICAgICAgICAgICAgICAgICAgcGlwMyBpbnN0YWxsIHgtbXJveS0xMDQ2CiAgICAgICAgICAgICAgICAgICAgcGlwMyBpbnN0YWxsIHgtbXJveS0xMDQ3CiAgICAgICAgICAgICAgICAgICAgcGlwMyBpbnN0YWxsIHgtbXJveS0xMDQ4CiAgICAgICAgICAgICAgICAgICAgZWNobyAiQnVpbGRGbGFnIiA+PiAvZXRjL2lidWlsZAogICAgICAgICAgICAgICAgICAgIGNhdCA8PCBFT0YgPj4gL2V0Yy9zaGFkb3dzb2Nrcy5qc29uCnsKICAgICJzZXJ2ZXIiOiIwLjAuMC4wIiwKICAgICJwb3J0X3Bhc3N3b3JkIjogewogICAgICAgICIxMzAwMSI6ICJ0aGVmb29saXNoMSIsCiAgICAgICAgIjEzMDAyIjogInRoZWZvb2xpc2gyIiwKICAgICAgICAiMTMwMDMiOiAidGhlZm9vbGlzaDMiLAogICAgICAgICIxMzAwNCI6ICJ0aGVmb29saXNoNCIsCiAgICAgICAgIjEzMDA1IjogInRoZWZvb2xpc2g1IiwKICAgICAgICAiMTMwMDYiOiAidGhlZm9vbGlzaDYiLAogICAgICAgICIxMzAwNyI6ICJ0aGVmb29saXNoNyIsCiAgICAgICAgIjEzMDA4IjogInRoZWZvb2xpc2g4IiwKICAgICAgICAiMTMwMDkiOiAidGhlZm9vbGlzaDkiLAogICAgICAgICIxMzAxMCI6ICJ0aGVmb29saXNoMTAiLAogICAgICAgICIxMzAxMSI6ICJ0aGVmb29saXNoMTEiLAogICAgICAgICIxMzAxMiI6ICJ0aGVmb29saXNoMTIiLAogICAgICAgICIxMzAxMyI6ICJ0aGVmb29saXNoMTMiCiAgICB9LAogICAgIndvcmtlcnMiOiAxNSwKICAgICJtZXRob2QiOiJhZXMtMjU2LWNmYiIKfQpFT0YKICAgICAgICAgICAgICAgICAgICBzc3NlcnZlciAtYyAvZXRjL3NoYWRvd3NvY2tzLmpzb24gLWQgc3RhcnQKICAgICAgICAgICAgICAgICAgICB4LXJlbGF5IHN0YXJ0CiAgICAgICAgICAgICAgICAgICAgZXhpdCAwCiAgICAgICAgICAgICAgICAgZWxzZQogICAgICAgICAgICAgICAgICAgIGFwdCBpbnN0YWxsIC15IHB5dGhvbjMtcGlwIHB5dGhvbjMtc2V0dXB0b29scwogICAgICAgICAgICAgICAgICAgIHBpcDMgaW5zdGFsbCAtVSBnaXQraHR0cHM6Ly9naXRodWIuY29tL3NoYWRvd3NvY2tzL3NoYWRvd3NvY2tzLmdpdEBtYXN0ZXIKICAgICAgICAgICAgICAgICAgICBwaXAzIGluc3RhbGwgeC1tcm95LTEwNDUKICAgICAgICAgICAgICAgICAgICBwaXAzIGluc3RhbGwgeC1tcm95LTEwNDYKICAgICAgICAgICAgICAgICAgICBwaXAzIGluc3RhbGwgeC1tcm95LTEwNDcKICAgICAgICAgICAgICAgICAgICBwaXAzIGluc3RhbGwgeC1tcm95LTEwNDgKICAgICAgICAgICAgICAgICAgICBlY2hvICJCdWlsZEZsYWciID4+IC9ldGMvaWJ1aWxkCiAgICAgICAgICAgICAgICAgICAgY2F0IDw8IEVPRiA+PiAvZXRjL3NoYWRvd3NvY2tzLmpzb24KewogICAgInNlcnZlciI6IjAuMC4wLjAiLAogICAgInBvcnRfcGFzc3dvcmQiOiB7CiAgICAgICAgIjEzMDAxIjogInRoZWZvb2xpc2gxIiwKICAgICAgICAiMTMwMDIiOiAidGhlZm9vbGlzaDIiLAogICAgICAgICIxMzAwMyI6ICJ0aGVmb29saXNoMyIsCiAgICAgICAgIjEzMDA0IjogInRoZWZvb2xpc2g0IiwKICAgICAgICAiMTMwMDUiOiAidGhlZm9vbGlzaDUiLAogICAgICAgICIxMzAwNiI6ICJ0aGVmb29saXNoNiIsCiAgICAgICAgIjEzMDA3IjogInRoZWZvb2xpc2g3IiwKICAgICAgICAiMTMwMDgiOiAidGhlZm9vbGlzaDgiLAogICAgICAgICIxMzAwOSI6ICJ0aGVmb29saXNoOSIsCiAgICAgICAgIjEzMDEwIjogInRoZWZvb2xpc2gxMCIsCiAgICAgICAgIjEzMDExIjogInRoZWZvb2xpc2gxMSIsCiAgICAgICAgIjEzMDEyIjogInRoZWZvb2xpc2gxMiIsCiAgICAgICAgIjEzMDEzIjogInRoZWZvb2xpc2gxMyIKICAgIH0sCiAgICAid29ya2VycyI6IDE1LAogICAgIm1ldGhvZCI6ImFlcy0yNTYtY2ZiIgp9CkVPRgogICAgICAgICAgICAgICAgICAgIHNzc2VydmVyIC1jIC9ldGMvc2hhZG93c29ja3MuanNvbiAtZCBzdGFydAogICAgICAgICAgICAgICAgICAgIHgtcmVsYXkgc3RhcnQKICAgICAgICAgICAgICAgICAgICBleGl0IDAKICAgICAgICAgICAgICAgICBmaQogICAgICAgIGZpCiAgICBmaQpmaQoKZWNobyAiY29tbWFuZCBweXRob24gY2FuJ3QgYmUgdXNlZC5zdGFydCBpbnN0YWxsaW5nIHB5dGhvbjMuNi4iCmNkIC90bXAKICAgIGlmIFsgLWYgL3RtcC9QeXRob24tMy42LjEudGd6IF07dGhlbgogICAgICBybSAvdG1wL1B5dGhvbi0zLjYuMS50Z3o7CiAgICBmaQp3Z2V0IGh0dHBzOi8vd3d3LnB5dGhvbi5vcmcvZnRwL3B5dGhvbi8zLjYuMS9QeXRob24tMy42LjEudGd6CnRhciAtenh2ZiBQeXRob24tMy42LjEudGd6CmNkIFB5dGhvbi0zLjYuMQpta2RpciAvdXNyL2xvY2FsL3B5dGhvbjMKLi9jb25maWd1cmUgLS1wcmVmaXg9L3Vzci9sb2NhbC9weXRob24zCm1ha2UKbWFrZSBpbnN0YWxsCmlmIFsgLWYgL3Vzci9iaW4vcHl0aG9uMyBdO3RoZW4KICAgcm0gL3Vzci9iaW4vcHl0aG9uMzsKICAgcm0gL3Vzci9iaW4vcGlwMzsKZmkKCmlmIFsgLWYgL3Vzci9iaW4vbHNiX3JlbGVhc2UgXTt0aGVuCiAgcm0gL3Vzci9iaW4vbHNiX3JlbGVhc2U7CmZpCgpsbiAtcyAvdXNyL2xvY2FsL3B5dGhvbjMvYmluL3B5dGhvbjMgL3Vzci9iaW4vcHl0aG9uMwpsbiAtcyAvdXNyL2xvY2FsL3B5dGhvbjMvYmluL3BpcDMgL3Vzci9iaW4vcGlwMwoKZWNobyAnZXhwb3J0IFBBVEg9IiRQQVRIOi91c3IvbG9jYWwvcHl0aG9uMy9iaW4iJyA+PiB+Ly5iYXNocmMKCnBpcDMgaW5zdGFsbCAtVSBnaXQraHR0cHM6Ly9naXRodWIuY29tL3NoYWRvd3NvY2tzL3NoYWRvd3NvY2tzLmdpdEBtYXN0ZXIKcGlwMyBpbnN0YWxsIHgtbXJveS0xMDQ1CnBpcDMgaW5zdGFsbCB4LW1yb3ktMTA0NgpwaXAzIGluc3RhbGwgeC1tcm95LTEwNDcKcGlwMyBpbnN0YWxsIHgtbXJveS0xMDQ4CgplY2hvICJCdWlsZEZsYWciID4+IC9ldGMvaWJ1aWxkCmNhdCA8PCBFT0YgPj4gL2V0Yy9zaGFkb3dzb2Nrcy5qc29uCnsKICAgICJzZXJ2ZXIiOiIwLjAuMC4wIiwKICAgICJwb3J0X3Bhc3N3b3JkIjogewogICAgICAgICIxMzAwMSI6ICJ0aGVmb29saXNoMSIsCiAgICAgICAgIjEzMDAyIjogInRoZWZvb2xpc2gyIiwKICAgICAgICAiMTMwMDMiOiAidGhlZm9vbGlzaDMiLAogICAgICAgICIxMzAwNCI6ICJ0aGVmb29saXNoNCIsCiAgICAgICAgIjEzMDA1IjogInRoZWZvb2xpc2g1IiwKICAgICAgICAiMTMwMDYiOiAidGhlZm9vbGlzaDYiLAogICAgICAgICIxMzAwNyI6ICJ0aGVmb29saXNoNyIsCiAgICAgICAgIjEzMDA4IjogInRoZWZvb2xpc2g4IiwKICAgICAgICAiMTMwMDkiOiAidGhlZm9vbGlzaDkiLAogICAgICAgICIxMzAxMCI6ICJ0aGVmb29saXNoMTAiLAogICAgICAgICIxMzAxMSI6ICJ0aGVmb29saXNoMTEiLAogICAgICAgICIxMzAxMiI6ICJ0aGVmb29saXNoMTIiLAogICAgICAgICIxMzAxMyI6ICJ0aGVmb29saXNoMTMiCiAgICB9LAogICAgIndvcmtlcnMiOiAxNSwKICAgICJtZXRob2QiOiJhZXMtMjU2LWNmYiIKfQpFT0YKCnNzc2VydmVyIC1jIC9ldGMvc2hhZG93c29ja3MuanNvbiAtZCBzdGFydAp4LXJlbGF5IHN0YXJ0
"""

def gprint(*args,pc='green', cc=None, **kwargs):
    print(colored("[+]",pc, attrs=['bold']), colored(" ".join([str(i) for i in args]),cc) ,**kwargs)

def show(data, tab=0):
    gprint("result", cc='red')
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    if isinstance(data, dict):
        for k in data:
            if isinstance(data[k], dict):
                print(k,":")
                show(data[k],tab=tab+2)
            else:
                cprint(tab* ' '  + "{} => {} ".format(k, data[k]), "yellow")
    else:
        gprint(data)

APIURL="https://api.vultr.com/v1/"

API_LIST = [
    "account/info",
    "app/list",
    "auth/info",
    "backup/list",
    # create server
    "os/list",
    "regions/list",
    "plans/list",
    "server/list",
    "baremetal/list",
    "startupscript/list"
]

def create_one(api,**kwargs):
    url = APIURL + "server/create"
    options = {
        "DCID":None,
        "VPSPLANID": None,
        "OSID": None,
        "label": None,
    }
    options.update(kwargs)
    for k in options:
        if not options[k]:
            gprint("Not set {}".format(k), pc="red")
            return None
    con = Connection(url, tp='http')
    con.options(headers={"API-Key": api})
    con.post(data=options, callback=show)


def destroy_one(api, id):
    url = APIURL + "server/destroy"
    options = {
        "SUBID" : id,
    }
    con = Connection(url, tp='http')
    con.options(headers={"API-Key": api})
    con.post(data=options, callback=show)

def update_db(data):
    db = Cache(DB_PATH)
    if isinstance(data, bytes):
        d = json.loads(data)
    else:
        d = data.json()
    s_clound = {d[i]['main_ip']:d[i]  for i in d}
    hs_clound = s_clound.keys()
    hs_now = [i.host for i in db.query(Host)]
    hs = []
    ds = set(hs_now) - set(hs_clound)
    ns = set(hs_clound) - set(hs_now)
    Dir  = os.path.join(os.path.dirname(DB_PATH), "shadowsocks")
    for n in ns:
        vars = s_clound[n]
        hs.append(Host(host=vars['main_ip'],passwd=vars['default_password'], port='22', user='root', location=vars['location'],os=vars['os'], disk=vars['disk'],vcpu_count=vars['vcpu_count'],cost_per_month=vars['cost_per_month']))
        gprint(vars['main_ip'], ' V')
        # if os.path.exists(path):
        fname = vars['location']+".json"
        fs = os.listdir(Dir)
        if fname in fs:
            c = 1
            while 1:
                
                if (fname + str(c)) not in fs:
                    fname += str(c)
                    break
                else:
                    c += 1
        print(fname, " -> local")

        with open(os.path.join(Dir, fname),'w') as fp:
            json.dump({
                "server":vars['main_ip'],
                'server_port':13003,
                'password':'thefoolish3',
                'method':'aes-256-cfb',
                'local_port':'1080'
                }, fp)
        
    for h in ds:
        print("x",h)
        e = db.query_one(Host, host=h)
        db.delete(e)
    for h in hs:
        h.save(db)



class Controll(cmd.Cmd):


    def __init__(self, token=None):
        super().__init__()
        self.prompt = colored(">", 'yellow', attrs=['bold'])
        self.api_key = token
        if not token:
            self.api_key = getpass.getpass()
        self.SUBID = ""
        self.OSID = '270'
        self.DCID = '25'
        self.PLANID = '201'
        self.SCRIPTID = ''
        self.label = 'jp-os'


    def do_exit(self, text):
        return True



    def do_show(self, text):
        for k in ['OSID', 'DCID', 'SUBID', 'PLANID', 'label']:
            gprint(k,"=", getattr(self, k))

    def do_set(self, text):
        if not '=' in text:
            gprint("must k = v")
            return
        k,v = text.split("=", 1)
        gprint(k,v)
        setattr(self,k.strip(),v.strip())

    def complete_set(self, text, line, begin, end):
        e = []
        for k in ['OSID', 'DCID', 'SUBID', 'PLANID', 'label']:
            if text in k:
                e.append(k)
        return e

    def do_create_script(self, file):
        t = base64.b64decode(INIT_PAYLOAD).decode("utf8")
        if  os.path.exists(file):
            with open(file) as fp:
                t = fp.read()
        con = Connection(APIURL + "startupscript/create", tp='http')
        con.options(headers={'API-Key': self.api_key})
        con.post(data={
                'name':'script',
                'script':t
            }, callback=show)

    def do_update(self, text):
        con = Connection(APIURL + "server/list", tp='http')
        con.options(headers={'API-Key': self.api_key})
        con.get(callback=update_db)

    def do_get(self, uri):
        con = Connection(APIURL + uri, tp='http')
        con.options(headers={'API-Key': self.api_key})
        con.get(callback=show)


    def do_create_server(self, text):
        if not text:
            text = "x"
        if not self.SCRIPTID:
            yn = input("scirpt id : null. do you want to use a scirpt id as startup scirpt? [y/n]").strip()
            if yn in ['','y', 'Y']:
                ids = requests.get(APIURL + "startupscript/list", headers={"API-Key": self.api_key}).json()
                while 1:
                    c = input("\nid:".join(ids.keys()) +"\nsee id [s:num] | use id [num]\n>")
                    if ':' in c:
                        c = c.split(":").pop()
                        cprint(ids[c]['script'], 'magenta')
                    elif re.match(r'^\d+$', c) and c in ids:
                        self.SCRIPTID = c
                        break
                    else:
                        cprint("try again !", 'red')


        create_one(self.api_key,**{
            "DCID": self.DCID,
            "OSID": self.OSID,
            "VPSPLANID" : self.PLANID,
            "SCRIPTID": self.SCRIPTID,
            "label": text,
        })

    def do_destroy(self, subid):
        if not self.SUBID:
            gprint("must set a valid subid")
            return False
        destroy_one(self.api_key, self.SUBID)

    def complete_get(self, text, line, begin, end):
        e = []
        for i in API_LIST:
            if text in i:
                e.append(i)
        return e

    def do_apilist(self, text):
        for i in API_LIST:
            gprint(i)

def main():
    c = Controll()
    c.cmdloop()

if __name__ == '__main__':

    main()
