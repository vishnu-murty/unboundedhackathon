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
    port=_("PRAVEGA_PORT", 9090, int),
    scope=_("PRAVEGA_SCOPE", "dell-scope9"),
    stream=_("PRAVEGA_STREAM", "dell-stream9"),
    group=_("PRAVEGA_READER_GROUP", "rg0"),
    reader_id=_("PRAVEGA_READER_ID", "rdr")
)

