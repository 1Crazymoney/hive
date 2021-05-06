from .node_api.node_apis import Apis

class MainNet:
    def __init__(self):
        self.api = Apis(self)

    def send(self, method, params=None, jsonrpc='2.0', id=1):
        message = {
            'jsonrpc': jsonrpc,
            'id': id,
            'method': method,
        }

        if params is not None:
            message['params'] = params

        from . import communication
        return communication.request('https://api.hive.blog:443', message)
