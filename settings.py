# Default settings

import os
# Internal
from utils.context import Context


def _(name, default, cast=str):
    return cast(os.environ.get(name, default))

es = Context(
    host=_("ELASTIC_HOST", "100.102.128.28"),
    port=_("ELASTIC_PORT", 8080, int),
    index=_("ELASTIC_INDEX", "pravega_telemetry")
)


pravega = Context(
    host=_("PRAVEGA_HOST", "100.64.25.48"),
    port=_("PRAVEGA_PORT", 9090, int),
    scope=_("PRAVEGA_SCOPE", "dell-scope8"),
    stream=_("PRAVEGA_STREAM", "dell-stream8"),
    group=_("PRAVEGA_READER_GROUP", "rg0"),
    reader_id=_("PRAVEGA_READER_ID", "rdr")
)

