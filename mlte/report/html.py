"""
mlte/report/html.py

Utilities for HTML report generation.
"""

import json
import socket
import tempfile
from typing import Any, Dict
from urllib import request

# The endpoint for resolving endpoints for report generation
RESOLUTION_ENDPOINT = "https://raw.githubusercontent.com/mlte-team/mlte/master/assets/endpoints.txt"  # noqa
# The local endpoint
LOCAL_ENDPOINT = "http://localhost:8000/html"


def _connected(host: str = "8.8.8.8", port: int = 53, timeout: int = 2) -> bool:
    """
    Determine if internet connectivity is available.

    :param host: The host used to test connectivity
    :type host: str
    :param port: The port used to test connectivity
    :type port: int
    :param timeout: The connection timeout
    :type timeout: int

    :return `True` if connected to the internet, `False` otherwise
    :rtype: bool
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


def _resolve_endpoint(
    local: bool, meta_endpoint: str = RESOLUTION_ENDPOINT
) -> str:
    """
    Resolve the endpoint for report generation.

    :param local: Indicates to resolve to local address
    :type local: bool
    :param meta_endpoint: The endpoint for resolution requests
    :type meta_endpoint: str

    :return: A report generation endpoint
    :rtype: str

    :raises RuntimeError: If unable to resolve endpoint
    """
    if local:
        return LOCAL_ENDPOINT
    with tempfile.NamedTemporaryFile() as f:
        path = f.name
        try:
            request.urlretrieve(meta_endpoint, path)
        except Exception:
            raise RuntimeError(
                "Unable to resolve endpoint for report generation."
            )

        with open(path, "r") as endpoints:
            # Return an arbitrary line from the list of endpoints
            for line in endpoints:
                return line.strip()

        raise RuntimeError("Unreachable")


def _generate_html(document: Dict[str, Any], local: bool) -> str:
    """
    Generate the HTML representation of a Report.

    :param document: The JSON document representation of the report
    :type document: Dict[str, Any]
    :param local: Indicates that the HTML generation server runs locally
    :type local: bool

    :return: The HTML representation of the report, as a string
    :rtype: str

    :raises RuntimeError: If report generation fails
    """
    assert _connected(), "Broken precondition."

    # Resolve the endpoint for report generation
    endpoint = _resolve_endpoint(local)

    # Construct the request with the report document
    req = request.Request(
        endpoint,
        method="POST",
        data=json.dumps(document).encode("utf-8"),
    )
    req.add_header("Content-Type", "application/json; charset=utf-8")

    with request.urlopen(req) as response:
        # TODO(Kyle): Better error handling.
        if response.status != 200:
            raise RuntimeError("Request failed.")
        return str(response.read().decode("utf-8"))