# Default settings

import os
# Internal
from utils.context import Context


def _(name, default, cast=str):
    return cast(os.environ.get(name, default))

es = Context(
    host=_("ELASTIC_HOST", "localhost"),
    port=_("ELASTIC_PORT", 8080, int),
    index=_("ELASTIC_INDEX", "pravega_telemetry")
)


pravega = Context(
    host=_("PRAVEGA_HOST", "localhost"),
    port=_("PRAVEGA_PORT", 9090, int)
)

pravega_reader = Context(
    scope=_("PRAVEGA_SCOPE", "dell-scope2"),
    stream=_("PRAVEGA_STREAM", "dell-stream2"),
    group=_("PRAVEGA_READER_GROUP", "rg1"),
    reader_id=_("PRAVEGA_READER_ID", "rdr9"),
)

