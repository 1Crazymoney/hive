from test_tools.node_api.api_base import ApiBase


class TagsApi(ApiBase):
    def __init__(self, node):
        super().__init__(node, 'tags_api')
