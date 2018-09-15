import pecan
from pecan import rest, response
from ipaddress import ip_interface as interf
import subprocess
from svcsys.common.validip import is_valid_ip
from svcsys.common.sed import sed_inplace
from svcsys.common.nicinfo import get_local_interfaces
import json


SIP_CONFIG_PATH="/sip_config/kamailio/kamailio.cfg"


SIP_CONT = "svc-sipserver"
EDGE_CONT = "svc-rtpproxy"
MCU_CONT = "svc-mcu"
CONT_MAP = {"sip": SIP_CONT, "edge": EDGE_CONT, "mcu": MCU_CONT}
DOCKER_GET_IP = 'docker inspect %s --format="{{.NetworkSettings.Networks.pub_net.IPAMConfig.IPv4Address}}"'


#!define ADDR_INTERNAL "172.21.0.121"
# direction.edge="172.21.0.120" desc "Edge Server Local IP Address"
# $var(ret)=t_relay_to_udp("172.21.0.120","5060");
# $var(ret)=t_relay_to_tcp("172.21.0.120","5060");
#    $var(confsrvip)="172.21.0.119";
SIP_IP_RES = [(re.compile(r'(#!define ADDR_INTERNAL )"[\d.]{7,15}"'),
               r'\g<1>"%(sip)s"'),
               (re.compile(r'(direction.edge=)"[\d.]{7,15}"(.*)'),
               r'\g<1>"%(edge)s"\g<2>'),
               (re.compile(r'(\$var.*=t_relay_to_udp\()"[\d.]{7,15}",("\d{4,20}"\);)'),
               r'\g<1>"%(edge)s",\g<2>'),
               (re.compile(r'(\$var.*=t_relay_to_tcp\()"[\d.]{7,15}",("\d{4,20}"\);)'),
               r'\g<1>"%(edge)s",\g<2>'),
               (re.compile(r'(.*\$var\(confsrvip\)=)"[\d.]{7,15}";'),
               r'\g<1>"%(mcu)s";'),]

# ips = {"sip": "111.111.111.113", "edge": "2.2.2.2", "mcu": "3.3.3.3"}


def compare_network(a, b):
    try:
        return interf(u"%s" % a).network == interf(u"%s" % b).network
    except Exception as e:
        return False


def is_sub_network(ip, net):
    try:
        return interf(u"%s" % ip).network.subnet_of(interf(u"%s" % net).network)
    except Exception as e:
        return False


IPCONF_PATH = "/etc/svc-server/svc_ips.conf"


def syscall(*args, **kwargs):
    process = subprocess.Popen(*args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, **kwargs)
    output, err = process.communicate()
    retcode = process.poll()
    return retcode, output, err


def net_info():
    cmd = 'docker network inspect pub_net --format "{{json .IPAM.Config}}"'
    r, o, e = syscall(cmd, shell=True)
    if r != 0 or "Error response from daemon" in e:
        return {}
    infos = json.loads(o)
    if infos:
        return infos[0]
    return {}


RM_DOCKER_CMDS = [
"echo 'Hello world, this is a test!'",
# "docker stop svc-sipserver",
"docker rm -f svc-sipserver",
# "docker stop svc-rtpproxy",
"docker rm -f svc-rtpproxy",
# "docker stop svc-mcu",
"docker rm -f svc-mcu"
]

RM_DOCKER_NETWOEK = [
"docker network rm pub_net"]

DOCKER_NETWOEK = [
"docker network create -d macvlan --subnet=%(subnet)s --gateway=%(gateway)s -o parent=%(nic)s pub_net"]

INSPECT_NETWORK_CMDS = [
"docker network inspect pub_net --format=\"{{.Name}}\"",
]
INSPECT_CMDS = [
"docker inspect svc-sipserver --format=\"{{.Name}}\"",
"docker inspect svc-rtpproxy --format=\"{{.Name}}\"",
"docker inspect svc-mcu --format=\"{{.Name}}\"",
]

RUN_CMDS = [
"docker run --name svc-sipserver --net=pub_net --ip=%(sip)s --privileged -e container=docker -v /sys/fs/cgroup:/sys/fs/cgroup sipserver:latest /usr/sbin/init &",
"docker run --name svc-rtpproxy --net=pub_net --ip=%(edge)s --privileged -e container=docker -v /sys/fs/cgroup:/sys/fs/cgroup rtpproxxy:latest /usr/sbin/init &",
"docker run --name svc-mcu --net=pub_net --privileged --restart always -e container=docker -v /mcu_config:/config mcu:latest /linuxrc &"
]

CREATE_CMDS = [
"docker create --name svc-sipserver --net=pub_net --ip=%(sip)s --privileged -e container=docker -v /sys/fs/cgroup:/sys/fs/cgroup sipserver:latest /usr/sbin/init",
"docker create --name svc-rtpproxy --net=pub_net --ip=%(edge)s --privileged -e container=docker -v /sys/fs/cgroup:/sys/fs/cgroup rtpproxxy:latest /usr/sbin/init",
"docker create --name svc-mcu --net=pub_net --privileged --restart always -e container=docker -v /mcu_config:/config mcu:latest /linuxrc &"
]

# def is_valid_ip(ip):
#     from IPy import IP
#     try:
#         IP(ip)
#     except Exception as e:
#         return False
#     return True

class SystemIPController(rest.RestController):

    @pecan.expose('json')
    def get_version(self):
        return {"api version": "1.0"}

    @pecan.expose(template='json')
    def get(self, **body):
        ips_key = ["host", "sip", "edge", "mcu", "subnet", "gateway"]
        ips = {}
        with open(IPCONF_PATH, "r") as f:
            for i in f.readlines():
                i = i.strip("\n")
                k, _, v = i.partition(":")
                ip = v
                err = False
                if "/" in v:
                    ip, _, pre = v.partition("/")
                    try:
                        ipre = int(pre)
                        if ipre > 32:
                            err = True
                    except Exception as e:
                        err = True
                if k in ips_key and is_valid_ip(ip) and not err:
                    ips[k] = v
            pub_net = net_info()
            gw = pub_net.get("Gateway")
            ips["gateway"] = gw if gw else None
            sn = pub_net.get("Subnet")
            ips["subnet"] = sn if sn else None
            r, o, e = syscall(DOCKER_GET_IP % CONT_MAP["sip"], shell=True)
            ips["sip"] = o if is_valid_ip(o) else None
            r, o, e = syscall(DOCKER_GET_IP % CONT_MAP["edge"], shell=True)
            ips["edge"] = o if is_valid_ip(o) else None
        response.status = 200
        return ips


    @pecan.expose(template='json')
    def post(self, **body):
        ips = body.get("systemips", {})
        support_ips = ["host", "sip", "edge", "mcu"]
        necessary_ips = ["host", "sip", "edge", "mcu"]
        missing = set(necessary_ips) - set(ips.keys())
        ips.setdefault("subnet", "172.21.0.0/24")
        ips.setdefault("gateway", "172.21.0.1")
        if missing:
            response.status = 400
            missings = ", ".join(missing)
            # pecan.response.text = u'Missing these ips in the context: %s.' % missings
            return {'message': 'Missing these ips in the context: %s.' % missings}
        sub_ip, _, pre = ips["subnet"].partition("/")
        try:
            ipre = int(pre)
            if ipre > 32:
                response.status = 400
                return {'message': 'Input invalid subnet: %s.' % ips["subnet"]}
        except Exception as e:
                response.status = 400
                return {'message': 'Input invalid subnet: %s.' % ips["subnet"]}
        for i in set(necessary_ips) & set(ips.keys()) | set(["subnet"]):
            ip = ips["subnet"].partition("/")[0] if i == "subnet" else ips[i]
            if not is_valid_ip(ip):
                response.status = 400
                return {'message': 'Input invalid %s ip: %s.' % (i, ip)}

        error = False
        emsg = []
        for k in support_ips + ["gateway"]:
            if not is_sub_network(ips[k], ips["subnet"]):
                response.status = 400
                return {'message': 'Error, %s: ip is not in subnet: %s.' % (k, ips["subnet"])}

        nic_infos = get_local_interfaces()
        product_evn = False
        nic = "eno1"
        for k, v in nic_infos.items():
            if k.startswith("eno") and is_sub_network(v, ips["subnet"]):
                product_evn = True
                nic = k
                break
        ips["nic"] = nic
        ip_content = []
        for k, v in ips.items():
            ip_content.append(":".join([k, v]))
        latency_ips = {}
        with open(IPCONF_PATH, "r") as f:
            for i in f.readlines():
                i = i.strip("\n")
                k, _, v = i.partition(":")
                if k in ips:
                    latency_ips[k] = v

        with open(IPCONF_PATH, "w+") as f:
            f.writelines("\n".join(ip_content))
        pub_net = net_info()
        cmds = []
        if pub_net.get("Gateway") != ips["gateway"] or pub_net.get("Subnet") != ips["subnet"]:
            cmds = RM_DOCKER_CMDS + RM_DOCKER_NETWOEK
        else:
            if latency_ips.get("sip") != ips["sip"]:
                cmds.append(RM_DOCKER_CMDS[1])
            if latency_ips.get("edge") != ips["edge"]:
                cmds.append(RM_DOCKER_CMDS[2])
        for cmd in cmds:
            r, o, e = syscall(cmd, shell=True)

        create_cmds = DOCKER_NETWOEK + CREATE_CMDS if product_evn else CREATE_CMDS
        inspect_cmds = INSPECT_NETWORK_CMDS + INSPECT_CMDS if product_evn else INSPECT_CMDS
        for i, cmd in enumerate(create_cmds):
            print cmd
            print "run command:\n  " + cmd % ips
            icmd = inspect_cmds[i]
            r, o, e = syscall(icmd, shell=True)
            if r == 0:
                continue
            r, o, e = syscall(cmd % ips, shell=True)
            print "Output:\n" + o
            print "Error Code: %s" % r
            print "Error:\n" + e
            if r != 0 or "Error response from daemon" in e:
                error = True
                if e:
                   emsg.append(e)
        if error:
            response.status = 500
            return {'message': "\n".join(emsg)}
            # print o
        # TODO: Create a new order, (optional) return some status data
        sed_inplace(SIP_CONFIG_PATH, SIP_IP_RES, **ips)
        response.status = 201
        return {'status': 'POST SUCCESS!\n'}
