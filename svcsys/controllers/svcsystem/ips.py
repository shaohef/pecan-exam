import pecan
from pecan import rest, response
import subprocess
from svcsys.common.validip import is_valid_ip


def syscall(*args, **kwargs):
    process = subprocess.Popen(*args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, **kwargs)
    output, err = process.communicate()
    retcode = process.poll()
    return retcode, output, err


CMDS= [
"echo 'Hello world, this is a test!'"
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
    def get(self):
        return {"api version": "1.0"}

    @pecan.expose(template='json')
    def post(self, **body):
        ips = body.get("systemips", {})
        support_ips = ["host", "sip", "edge", "mcu"]
        necessary_ips = ["host", "sip", "edge", "mcu"]
        missing = set(necessary_ips) - set(ips.keys())
        if missing:
            response.status = 400
            missings = ", ".join(missing)
            # pecan.response.text = u'Missing these ips in the context: %s.' % missings
            return {'message': 'Missing these ips in the context: %s.' % missings}
        for i in set(necessary_ips) & set(ips.keys()):
            if not is_valid_ip(ips[i]):
                response.status = 400
                return {'message': 'Input invalid %s ip: %s.' % (i, ips[i])}
        for cmd in CMDS:
            r, o, e = syscall(cmd, shell=True)
            if r != 0:
                response.status = 500
                return {'message': e}
            print o
        # TODO: Create a new order, (optional) return some status data
        response.status = 201
        return {'status': 'POST SUCCESS!\n'}
