from typing import Dict
import subprocess
import json as json_module
from pprint import pformat
from datetime import date, datetime
import logging

from au.common.datetime import date_to_local


logger = logging.getLogger(__name__)


def github_json_serializer(obj):
    if isinstance(obj, (date, datetime)):
        dt = date_to_local(obj)
        return dt.isoformat()
    raise TypeError(f"Type {type(obj)} not JSON serializable")


def github_json_deserializer(dct):
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                dct[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
    return dct


def gh(*args) -> subprocess.CompletedProcess:
    cmd = ["gh"]
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def gh_api(
    endpoint: str = None,
    method: str = None,
    query: str = None,
    **kwargs,
) -> Dict[str, any]:
    if query and endpoint and endpoint != "graphql":
        raise ValueError("If query is provided, the endpoint must be 'graphql'")
    elif query:
        endpoint = "graphql"
    cmd = ["gh", "api", endpoint, "--paginate"]
    if method:
        cmd.extend(["--method", method])
    for k, v in kwargs.values():
        if isinstance(v, bool):
            val = "true" if v else "false"
            cmd.extend(["-F", f"{k}={val}"])
        elif isinstance(v, int):
            cmd.extend(["-F", f"{k}={v}"])
        else:
            cmd.extend(["-f", f"{k}={str(v)}"])
    if query:
        cmd.extend(["-f", "query='{query}'"])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        json = json_module.loads(result.stdout, object_hook=github_json_deserializer)
        if isinstance(json, dict):
            if json.get("message", "").upper() == "NOT FOUND":
                logger.error(f"Invalid GitHub API Endpoint: {endpoint}")
                return None
        logger.debug(f"Retrieved JSON: {pformat(json)}")
        return json
    except subprocess.CalledProcessError:
        logger.info(f"No result returned for gh_api({endpoint})")
        return None
    except FileNotFoundError:
        logger.exception(f"Error trying to run `gh` command")
        return None
    except json_module.JSONDecodeError:
        logger.exception(f"Invalid JSON output from `gh` command")
        return None
