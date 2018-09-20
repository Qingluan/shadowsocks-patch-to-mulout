import json, os, time, sys,  atexit, signal
from asynctools.servers import TcpTests
from termcolor import colored
import random
import requests
import logging
from qlib.data import dbobj, Cache
import argparse

LOG_LEVEL=logging.ERROR
BASE_ROOT = os.path.expanduser("~/.config/")
ROOT = os.path.expanduser("~/.config/seed")
if not os.path.exists(BASE_ROOT):
    os.mkdir(BASE_ROOT)

if not os.path.exists(ROOT):
    os.mkdir(ROOT)

DB_PATH = os.path.expanduser("~/.config/seed/cache.db")



def loger(level=LOG_LEVEL):
    logging.basicConfig(level=level)
    return logging.getLogger(__file__)


log = loger()

def get_db():
    return Cache(DB_PATH)


SHADOWSOCKS_PATH = "/etc/shadowsocks"
SOURCE_SHADOWSOCKS_PATH = os.path.join(os.getenv("HOME"), ".config/seed/shadowsocks")

if not os.path.exists(SHADOWSOCKS_PATH):
    os.mkdir(SHADOWSOCKS_PATH)

def read_all_route(R):
    for r, ds, fs in os.walk(R):
        for f in fs:
            if "json" in f:
                with open(os.path.join(r, f)) as fp:
                    con = json.load(fp)
                    
                    m = "{}:{}".format(con['server'],con['server_port'])
                    # print("[+]",m)
                    yield m,con


def test_one_time():
    old = time.time()
    #print("[+] Read from local:", colored(old,'yellow'))
    all_routes = dict(read_all_route(SOURCE_SHADOWSOCKS_PATH))
    old2 = time.time()
    #print("[+] Read from local:", colored(old2 - old,'yellow'))
    res =  sorted(TcpTests([i for i in all_routes]), key=lambda x: x[1])
    for no,i in enumerate(res):
        with open(SHADOWSOCKS_PATH + "/{}.json".format(no), "w") as fp:
            json.dump(all_routes[i[0]],fp)
        print("[+]",colored(i[0],'green'))
    log.info(colored("[+]",'green') + " Test finish use time:" + colored(time.time() - old ,'yellow'))

def get():
    files = [i for i in os.listdir(SHADOWSOCKS_PATH) if i[0] in '0123456789']
    l = len(files)
    s = []
    for i in files:
        s += [i] * (l-int(i[0]))
    with open(os.path.join(SHADOWSOCKS_PATH,random.choice(s)),'rb') as fp:
        r = json.load(fp)
        if sys.version[0] == '2':
            return {i.encode("utf-8") : r[i].encode("utf-8")}
        else:
            return r

class Host(dbobj):
    pass

class Token(dbobj):
    pass

def sync(token=None):
    db = get_db()
    if not token:
        _ = db.query_one(Token)

        if _:
            token = _.token
        else:
            token = input("Token initialization:")
            t = Token(token=token)
            t.save(db)

    if not token:
        print('no token')
        return
    res = requests.get('https://api.vultr.com/v1/server/list', headers={
        'API-Key': token,
        }).json().values()
    
    ss = {}
    old_hosts = db.query(Host)
    [db.delete(i) for i in old_hosts]
    # old_hosts_hosts = {i.host:i for i in old_hosts}
    for i in res:
        s = Host(host=i['main_ip'],
            passwd=i['default_password'],
            port='22',
            user='root',
            location=i['location'],
            os=i['os'],
            disk=i['disk'],
            vcpu_count=i['vcpu_count'],
            cost_per_month=i['pending_charges']
        )
        ss[s.host] = s
        print(colored('sync : %s : %s' % (s.host, s.location), 'green'))
    # no = set(old_hosts_hosts.keys()) - set(ss.keys())
    # for i in old_hosts_hosts.keys():
        # db.delete(old_hosts_hosts[i])
        # print(colored('delete: %s' % i, 'red'))
    db.save_all(*list(ss.values()))

    Dir  = os.path.join(os.path.dirname(DB_PATH), "shadowsocks")
    if not os.path.exists(Dir):
        os.mkdir(Dir)
    for s in ss.values():
        fname = s.location+".json"
        fs = os.listdir(Dir)
        if fname in fs:
            c = 1
            while 1:
                
                if (fname + str(c)) not in fs:
                    fname += str(c)
                    break
                else:
                    c += 1
        print(colored(fname + " -> local", 'blue'))
        with open(os.path.join(Dir, fname),'w') as fp:
            json.dump({
                "server":s.host,
                'server_port':13003,
                'password':'thefoolish3',
                'method':'aes-256-cfb',
                'local_port':'1080'
                }, fp)



class Daemon:
    """A generic daemon class.

    Usage: subclass the daemon class and override the run() method."""

    def __init__(self, pidfile):
        self.pidfile = pidfile
        self.std = pidfile+".log"
        self.ste = pidfile+".err.log"

    def daemonize_mul(self, jobs):
        imTheFather = True
        children = []

        for job in jobs:
            child = os.fork()
            if child:
                children.append(child)
            else:
                imTheFather = False
                job()
                break

        # in the meanwhile 
        # ps aux|grep python|grep -v grep|wc -l == 11 == 10 children + the father

        if imTheFather:
            for child in children:
                os.waitpid(child, 0)

    def daemonize(self):
        """Deamonize class. UNIX double fork mechanism."""

        try:
            child = os.fork()
            is_child = False
            if child:
                # exit first parent

                sys.exit(0)
            else:
                is_child = True
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            child = os.fork()
            if child:

                # exit from second parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(self.ste, 'a+')
        se = open(self.std, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self.pidfile,'w+') as f:
            f.write(pid + '\n')

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon."""

        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile,'r') as pf:

                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = "pidfile {0} already exist. " + \
                    "Daemon already running?\n"
            sys.stderr.write(message.format(self.pidfile))
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon."""

        # Get the pid from the pidfile
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = "pidfile {0} does not exist. " + \
                    "Daemon not running?\n"
            sys.stderr.write(message.format(self.pidfile))
            return # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print (str(err.args))
                sys.exit(1)

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def run(self):
        """You should override this method when you subclass Daemon.

        It will be called after the process has been daemonized by
        start() or restart()."""
        pass

class AutoTestShadowsocks(Daemon):
    def __init__(self, *args, interval=60, **kwargs):
        super().__init__(*args, **kwargs)
        self.interval = interval

    def run(self):
        while 1:
            test_one_time()
            time.sleep(self.interval)

def auth_and_settoken(token):
    if len(token) == 36:
        try:
            res = requests.get("https://api.vultr.com/v1/account/info", headers={'API-Key': token}).json()
        
            c = Cache(DB_PATH)
            try:
                c.drop(Token)
            except Exception:
                pass
            tt = Token(token=token)
            tt.save(c)
            print(colored("[+]", 'green'), 'token -> ', token)
        except Exception as e:
            print(colored("[+]", 'red'), e)
    else:
        print(colored("[+]", 'red'), "len is error: ", token)

def sync_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--update', action='store_true',default=False,help='update hosts')
    parser.add_argument('-s','--server', default=None, help='start server / stop/ restart')
    parser.add_argument('-t','--token', default=None, help='set token.. ')
    parser.add_argument('-i','--interval', default=60, type=int, help="set server's interval.")

    args = parser.parse_args()
    interval = args.interval
    
    if args.token:
        auth_and_settoken(args.token)

    if args.update:
        sync(args.token)

    if args.server == 'start':
        while 1:
            test_one_time()
            time.sleep(interval)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--update', action='store_true',default=False,help='update hosts')
    parser.add_argument('-s','--server', default=None, help='start server / stop/ restart')
    parser.add_argument('-i','--interval', default=60, type=int, help="set server's interval.")

    args = parser.parse_args()
    interval = args.interval

    if interval < 30:
        print("[!] interval must set > 30 , you set : ", colored(interval,'yellow')) 
        return
    if args.update:
        sync()

    if args.server:
        d = AutoTestShadowsocks('/tmp/shadowsocks_test.pid', interval=interval)
        if args.server == 'start':
            d.start()
        elif args.server == 'stop':
            d.stop()
        elif args.server == 'restart':
            d.restart()
        log.info("Start service async socket")


if __name__ == '__main__':
    main()
    # for k,v in res:
        # print(colored(k,'green'),colored(v,'red'))
