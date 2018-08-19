import pecan
from pecan import rest, response

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
            return {'message': 'Missing these ips in the context: %s.' % missings}
        # TODO: Create a new order, (optional) return some status data
        response.status = 201
        return {'status': 'POST SUCCESS!\n'}

