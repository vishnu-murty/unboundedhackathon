"""
Context class
"""


class Context(dict):
    """Dictionary elements accessed using object notation"""

    def __init__(self, *args, **kwargs):
        """Constructor for the context object"""

        super(Context, self).__init__(*args, **kwargs)
        self.__dict__ = self


if __name__ == "__main__":
    from pprint import pprint

    json = Context(name="Name", description="Description")
    pprint(json)

    json.name = "This is a new name"
    pprint(json)

    json.description = "This is a cool description"
    json.version = '0.0.1'
    pprint(json)
