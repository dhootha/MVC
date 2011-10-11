import sys
import os
import shutil
import unittest
import httplib
import urllib
import time
import platform
import StringIO
from sikuli.Sikuli import *

import sg59_apple_devs
import sg60_android_devs
import sg61_other_devs_formats

   
def get_os_name():
    """Returns the os string for the SUT
    """
    if "MAC" in str(Env.getOS()):
        return "osx"
    elif "WINDOWS" in str(Env.getOS()):
        return "win"
    elif "LINUX" in str(Env.getOS()):
        return "lin"
    else:
        print ("I don't know how to handle platform '%s'", Env.getOS())

HEADER="""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<litmusresults action="submit" useragent="UberSikuliAgent/1.0 (machine foobar)" machinename="sikuli_machine">
   <testresults
   username="jed@pculture.org"
   authtoken="sik-machine"
   product="MVC"
   platform="%(opsys)s"
   opsys="%(platform)s"  
   branch="git-Master"
   buildid="%(buildid)s"
   locale="en-US"
   >
   """

STORY ="""<result testid="%(testid)s"
    is_automated_result="0"
    resultstatus="%(status)s"
    exitstatus="0"
    timestamp="%(timestamp)s"
    >
        <comment><![CDATA[ %(error_msg)s]]>
        </comment>
    </result>
"""

FOOTER = """</testresults>
</litmusresults>
"""


def set_test_id(test_id):
    tid = test_id.split()
    s = str(tid[0]).strip(">,<,[,]")
    L = s.split('_')
    testid = L.pop()
    return testid


def set_status(stat):
    print stat
    if stat == ".":
        status = "pass"
    else:
        status = "fail"
    return status


def get_linux_os():
    UBUNTU_DICT = {"10.04":"Ubuntu (Lucid)",
                   "10.10":"Ubuntu (Maverick)",
                   "11.04":"Ubuntu (Natty)"}
    f = open("/etc/issue",'r')
    info = f.read()
    f.close()
    v,r,_,_ = info.split()
    if v == "Ubuntu":
        plat = UBUNTU_DICT[r]
    else:
        plat = "generic"
    return plat

def set_litmus_os():
    """Returns the os string for the SUT using the Sikuli way).

    """
    WINDOWS_VERS = {"5":"XP",
                    "6":"Vista",
                    "7":"Windows 7"}
    test_os = get_os_name()
    if str(test_os) == "osx":
##        v, _, _ = platform.mac_ver()
##        v = str('.'.join(v.split('.')[:2]))
        lit_os = ["OS X", "10.6"]
        return lit_os
    elif str(test_os) == "win":
        ver = Env.getOSVersion()
        wv = ver.split('.')[0]
        v = WINDOWS_VERS[wv]
        lit_os = ["Windows",v]
        return lit_os
    elif str(test_os) == "lin":
        plat = get_linux_os()
        lit_os = ["Linux",plat]
        return lit_os
        
    else:
        print ("I don't know how to handle platform '%s'", test_os)      


def write_log(log,testid,stat,error_info=""):
    tid = set_test_id(testid)
    status = set_status(stat)
    if status == "pass":
        error_comment = ""
    else:
        error_comment = error_info.split("----------------------------------------------------------------------")[1]
    if not tid == "001setup" or tid == "999reset":
        f = open(log, 'a')
        f.write(STORY % {"testid": tid,
                         "status": status,
                         "timestamp": time.strftime("%Y%m%d%H%M%S", time.gmtime()),
                         "error_msg": error_comment
                             })
        f.close()
        time.sleep(3)

def write_footer(log):
    f = open(log, 'a')
    f.write(FOOTER)
    f.close()
    ts = time.strftime("%d%m%H%M%S", time.gmtime())
    fl = os.path.join(os.getcwd(),"last_run",ts+"_log.xml")
    if "WINDOWS" in str(Env.getOS()):
        shutil.copy(log,fl)
    else:
        shutil.move(log,fl)
    
def send_result(log):
    f = open(log)
    log_data = f.read()
    params = urllib.urlencode({'data':log_data,                               
                                })
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    conn = httplib.HTTPConnection("litmus.pculture.org")

    print "sending test result..."
    conn.request("POST", "/process_test.cgi", params, headers)
    response = conn.getresponse()
    data = response.read()
    print data
    conn.close()
    f.close()


def set_build_id():
#    build_id = "2011062299" #set custom build id here.
    build_id = time.strftime("%Y%m%d99", time.gmtime())
    return build_id

def write_header(log):
    (r,v) = set_litmus_os()
    f = open(log,'w')
    f.write(HEADER % {"buildid": set_build_id(),
                      "opsys": r,
                      "platform": v
                      })
    f.close()



class LitmusRunner(unittest.TestCase):
    def __init__(self,suite):
        print suite
        params = []
        self.litmus = True
        if "MVC_Suite" in str(suite):
            self.suite = unittest.TestLoader().loadTestsFromTestCase(suite)
        else:
            params = list(suite)
            subgroup = params[0]
            sg = subgroup.split('.sikuli')
            self.suite = unittest.TestSuite()
            for tc in params:
                if "test" in tc:
                    self.suite.addTests([unittest.defaultTestLoader.loadTestsFromName(sg[0]+'.MVC_Suite.'+tc)],)
                    
    def litmus_test_run(self):
        ts = time.strftime("%M%S", time.gmtime())
        log = "Log_current.xml"
        logfile = os.path.join(os.getcwd(),log)
        buf = StringIO.StringIO()
        runner = unittest.TextTestRunner(stream=buf)
        write_header(logfile)
        
        for x in self.suite:
            runner.run(x)
            # check out the output
            byte_output = buf.getvalue()
            id_string = str(x)
            stat = byte_output[0]
            write_log(logfile,id_string,stat,byte_output)
            buf.truncate(0)
        time.sleep(3)
        write_footer(logfile)
#        send_result(logfile)

