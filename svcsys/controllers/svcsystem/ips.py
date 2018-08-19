import pecan
from pecan import rest, response

class SystemIPController(rest.RestController):

    @pecan.expose('json')
    def get(self):
        return {"api version": "1.0"}

    @pecan.expose(template='json')
    def post(self, **kw):
        # TODO: Create a new order, (optional) return some status data
        response.status = 201
        print kw
        return {'status': 'POST SUCCESS!\n'}

