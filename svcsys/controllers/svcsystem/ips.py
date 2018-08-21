import pecan
from pecan import rest, response
import subprocess


def syscall(*args, **kwargs):
    process = subprocess.Popen(*args, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, **kwargs)
    output, err = process.communicate()
    retcode = process.poll()
    return retcode, output, err


CMDS= [
"echo 'Hello world, this is a test!'"
]


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
        for cmd in CMDS:
            r, o, e = syscall(cmd, shell=True)
            if r != 0:
                response.status = 500
                return {'message': e}
            print o
        # TODO: Create a new order, (optional) return some status data
        response.status = 201
        return {'status': 'POST SUCCESS!\n'}
