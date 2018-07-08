import os, re, time, sys, json, random
from termcolor import colored
BACKUP_PATH = os.path.join(os.getenv("HOME"),".config/shadowsocks-extension")
BACKUP_PATH_INFO = os.path.join(os.getenv("HOME"),".config/shadowsocks-extension.json")
BACKUP_PATH_INFO_CONFIG = os.path.join(os.getenv("HOME"),".config/shadowsocks-extension2.json")

if not os.path.exists(BACKUP_PATH):
    os.mkdir(BACKUP_PATH)



GET_P = """

## -*- patched-mark -*- 
SHADOWSOCKS_PATH = "/etc/shadowsocks" 
import json, os,sys
def get():
    files = [i for i in os.listdir(SHADOWSOCKS_PATH) if i[0] in '0123456789']
    l = len(files)
    s = []
    for i in files:
        s += [i] * (l-int(i[0]))
    with open(os.path.join(SHADOWSOCKS_PATH,random.choice(s)),'r') as fp:
        r = json.load(fp)
        if sys.version[0] == '2':
            d = dict()
            for i in r:
                if isinstance(r[i], unicode):
                    d[i.encode('utf-8')] = r[i].encode('utf-8')
                else:
                    d[i.encode('utf-8')] = r[i]
            return d
        else:
            return r

"""


USE_GET_P = """
        self._config = config
        if is_local and 'auto-choose' in config:
            C = get()
            self._config.update(C)
            config.update(C)
            logging.info("Choose: %s" % self._config['server'])
"""

USE_CONFIG_P = """config['server_port'] = int(value)
## -*- patched-mark -*- 
            elif key == '--auto-choose':
                logging.info("mew mew mew")
                config['auto-choose'] = True
"""

USE_CONFIG2_P = """longopts = ['help', 'auto-choose',"""

key_1 = "self._config = config"
key_2 = "class"
key_3 = "config['server_port'] = int(value)"
key_4 = "longopts = ['help',"

def patch_config(files):
    all_tcp_files = [i.replace('tcprelay.py', 'shell.py') for i in files]
    smap = {}
    print(colored("[+] backup ", 'green'))
    for file in all_tcp_files:
        if not file.strip(): continue
        qf = time.asctime().replace(" ", "_") + str(random.random())
        smap[qf] = file
        back_file = os.path.join(BACKUP_PATH, qf)
        os.system("cp %s %s" %(file, back_file))
    with open(BACKUP_PATH_INFO_CONFIG, 'w') as fp:
        json.dump(smap, fp)
    time.sleep(2)

    print(colored("[+] patch ","green"))
    for file in all_tcp_files:
        if not file.strip(): continue
        content = ''
        with open(file) as fp:
            content = fp.read()
            if "## -*- patched-mark -*- " in content:
                print(colored("[!]", 'yellow'), file, 'patched !!')
                continue

            f = content.find(key_4)
            lc = content[:f]
            rc = content[f+ len(key_4):]
            content = lc + USE_CONFIG2_P + rc

            f = content.find(key_3)
            lc = content[:f]
            rc = content[f+ len(key_3):]
            content = lc + USE_CONFIG_P + rc
        if content:
            with open(file, "w") as fp:
                fp.write(content)
        print("[+]", "patch file:", file)
    print(colored("[+]",'green'), "--- ok ---")

def patch(files):
    all_tcp_files = files
    smap = {}
#    if not os.listdir(BACKUP_PATH):
    print(colored("[+] backup ", 'green'))
    for file in all_tcp_files:
        if not file.strip(): continue
        qf = time.asctime().replace(" ", "_") + str(random.random())
        smap[qf] = file
        back_file = os.path.join(BACKUP_PATH,  qf)
        os.system("cp %s %s" %(file, back_file))
    with open(BACKUP_PATH_INFO, 'w') as fp:
        json.dump(smap, fp)
    time.sleep(2)

    print(colored("[+] patch ","green"))
    for file in all_tcp_files:
        if not file.strip(): continue
        content = ''
        with open(file) as fp:
            content = fp.read()
            if "## -*- patched-mark -*- " in content:
                print(colored("[!]", 'yellow'), file, 'patched !!')
                continue
            f = content.find(key_2)
            lc = content[:f]
            rc = content[f:]
            content = lc + GET_P + rc

            f = content.find(key_1)
            lc = content[:f]
            rc = content[f+ len(key_1):]
            content = lc + USE_GET_P + rc
        if content:
            with open(file, "w") as fp:
                fp.write(content)
        print("[+]", "patch file:", file)
    print(colored("[+]",'green'), "--- ok ---")

def backup():
    smap = None
    with open(BACKUP_PATH_INFO) as fp:
        smap = json.load(fp)
    
    
    if smap:
        for dst, fr in smap.items():
            os.popen("cp %s %s " % (os.path.join(BACKUP_PATH,dst),  fr))
            print(colored("[+]", 'green'), 'backup : ', dst, ' -> ', fr)

    smap2 = None
    with open(BACKUP_PATH_INFO_CONFIG) as fp:
        smap2 = json.load(fp)

    
    if smap2:
        for dst, fr in smap2.items():
            os.popen("cp %s %s " % (os.path.join(BACKUP_PATH,dst), fr))

            print(colored("[+]", 'green'), 'backup : ', dst, ' -> ', fr)


def main():
    if sys.argv[1] == 'patch':
        files = os.popen('find / -name "*tcprelay.py" -type f ').read().split("\n")
        patch(files)
        patch_config(files)
    elif sys.argv[1] == 'backup':
        backup()
    else:
        print(colored("[!]", 'red') , 'only support backup/patch')


