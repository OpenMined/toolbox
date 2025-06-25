from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from toolbox.installed_mcp import InstalledMCP
from toolbox.store.store_code import STORE_ELEMENTS


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNKNOWN = "unknown"
    UNHEALTHY = "unhealthy"


def healthcheck(mcp: "InstalledMCP") -> HealthStatus:
    try:
        res = STORE_ELEMENTS[mcp.name].healthcheck(mcp)
        if res:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNHEALTHY
    except NotImplementedError:
        return HealthStatus.UNKNOWN
    except Exception:
        import traceback

        traceback.print_exc()
        return HealthStatus.UNHEALTHY
