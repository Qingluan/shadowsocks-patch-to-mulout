import json, os, time, sys,  atexit, signal
from asynctools.servers import TcpTests
from termcolor import colored
import random
import logging

LOG_LEVEL=logging.ERROR

def loger(level=LOG_LEVEL):
    logging.basicConfig(level=level)
    return logging.getLogger(__file__)


log = loger()

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



def main():
    interval = 60
    if len(sys.argv) > 2:
        interval = int(sys.argv[2])
        if interval < 30:
            print("[!] interval must set > 30 , you set : ", colored(interval,'yellow')) 
    d = AutoTestShadowsocks('/tmp/shadowsocks_test.pid', interval=interval)
    if sys.argv[1] == 'start':
        d.start()
    elif sys.argv[1] == 'stop':
        d.stop()
    elif sys.argv[1] == 'restart':
        d.restart()
    log.info("Start service async socket")


if __name__ == '__main__':
    main()
    # for k,v in res:
        # print(colored(k,'green'),colored(v,'red'))
