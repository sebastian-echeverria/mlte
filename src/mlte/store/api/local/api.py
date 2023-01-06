"""
Result persistence API for local filesystem.
"""

import json
from pathlib import Path
from typing import Optional, Set, Dict, Any

from .data_model import (
    Result,
    ResultVersion,
)

# The prefix that indicates a local filesystem directory is used
LOCAL_URI_PREFIX = "local://"

"""
The overall structure for the directory hierarchy looks like:

root/
  model_identifier0/
    model_version0/
      result_identifier0.json

The data for an individual result is then stored within a JSON file.
The structure of this JSON file looks like:

{
    "identifier": "...",
    "tag": "...",
    "versions": [
        {"version": 0, "data": ...}
        {"version": 1, "data": ...}
        ...
    ]
}
"""

# -----------------------------------------------------------------------------
# Parsing Helpers
# -----------------------------------------------------------------------------


def _parse_root_path(uri: str) -> Path:
    """
    Parse the root path for the backend from the URI.

    :param uri: The URI
    :type uri: str

    :return: The parsed path
    :rtype: Path
    """
    assert uri.startswith(LOCAL_URI_PREFIX), "Broken precondition."
    path = Path(uri[len(LOCAL_URI_PREFIX) :])
    if not path.exists():
        raise RuntimeError(
            f"Root path for local artifact store {path} does not exist."
        )
    return path


# -----------------------------------------------------------------------------
# Metadata
# -----------------------------------------------------------------------------


def _available_result_versions(result_path: Path) -> Set[int]:
    """
    Get the available versions for a result.
    :param result_path: The path to the result
    :type result_path: Path
    :return: The available versions for the result
    :rtype: Set[int]
    """
    with open(result_path.as_posix(), "r") as f:
        document = json.load(f)
        return set(e["version"] for e in document["versions"])


def _result_path(model_version_path: Path, result_identifier: str):
    """
    Form the result path from model version path and result identifier.

    :param model_version_path: The path to the model version
    :type model_version_path: Path
    :param result_identifier: The identifier for the result
    :type result_identifier: str

    :return: The formatted result path
    :rtype: Path
    """
    path = (model_version_path / result_identifier).with_suffix(".json")
    return Path(str(path).replace(" ", "-"))


# -----------------------------------------------------------------------------
# Read
# -----------------------------------------------------------------------------


def _read_result(result_path: Path, version: Optional[int] = None) -> Result:
    """
    Read the data for an individual result.
    :param result_path: The path to the result
    :type result_path: Path
    :param version: The (optional) version identifier
    :type version: Optional[int]
    :return: The read result
    :rtype: Result
    """
    with result_path.open("r") as f:
        result = Result.from_json(json.load(f))

    # Ensure requested version is present
    assert (version is None) or (
        version in set(v.version for v in result.versions)
    ), "Broken invariant."

    # Filter to only include the version of interest
    # TODO(Kyle): Determine how we want to handle
    # multiversioning from user perspective / interface
    version = (
        max(_available_result_versions(result_path))
        if version is None
        else version
    )
    result.versions = [v for v in result.versions if v.version == version]

    return result


# -----------------------------------------------------------------------------
# Write
# -----------------------------------------------------------------------------


def _write_result(result_path: Path, result: Result, tag: Optional[str]):
    """
    Write a result to the file at `result_path`.
    :param result_path: The path to the result
    :type result_path: Path
    :param result: The result
    :type result: Result
    """
    if result_path.exists():
        new_version = max(_available_result_versions(result_path)) + 1

        # Read existing document
        with result_path.open("r") as f:
            mutating = Result.from_json(json.load(f))

        # Update tag
        mutating.tag = tag

        # Update result version
        mutating.versions.append(
            ResultVersion(version=new_version, data=result.versions[0].data)
        )

        # Persist updates
        with result_path.open("w") as f:
            json.dump(mutating.to_json(), f)
    else:
        with result_path.open("w") as f:
            json.dump(result.to_json(), f)


# -----------------------------------------------------------------------------
# API Interface
# -----------------------------------------------------------------------------


def read_result(
    uri: str,
    model_identifier: str,
    model_version: str,
    result_identifier: str,
    result_version: Optional[int] = None,
) -> Dict[str, Any]:
    """TODO(Kyle)"""
    root = _parse_root_path(uri)
    assert root.exists(), "Broken precondition."
    _check_exists(root, model_identifier, model_version)

    version_path = root / model_identifier / model_version
    assert version_path.exists(), "Broken invariant."

    result_path = _result_path(version_path, result_identifier)
    if not result_path.exists():
        raise RuntimeError(
            f"Failed to read result, "
            f"result with identifier {result_identifier} not found."
        )

    if (
        result_version is not None
        and result_version not in _available_result_versions(result_path)
    ):
        raise RuntimeError(
            f"Failed to read result, "
            f"requested version {result_version} not found."
        )

    result = _read_result(result_path, result_version)
    assert len(result.versions) == 1, "Broken invariant."
    return result.versions[0].data


def write_result(
    uri: str,
    model_identifier: str,
    model_version: str,
    result_identifier: str,
    result_data: Dict[str, Any],
    result_tag: Optional[str],
):
    """TODO(Kyle)"""
    root = _parse_root_path(uri)
    assert root.exists(), "Broken precondition."

    # Construct internal data model
    result = Result.from_json(
        {
            "identifier": result_identifier,
            "tag": result_tag if result_tag is not None else "",
            "versions": [{"version": 0, "data": result_data}],
        }
    )

    # Create model directory
    model_path = root / model_identifier
    if not model_path.exists():
        model_path.mkdir()

    # Create version directory
    version_path = model_path / model_version
    if not version_path.exists():
        version_path.mkdir()

    result_path = _result_path(version_path, result_identifier)
    _write_result(result_path, result, result.tag)


def _check_exists(
    root: Path, model_identifier: str, model_version: Optional[str] = None
):
    """
    Check if data is available for a particular model and version.
    :param root: The root path
    :type root: Path
    :param model_identifier: The model identifier
    :type model_identifier: str
    :param model_version: The model version
    :type model_version: Optional[str]
    """
    model_path = root / model_identifier
    if not model_path.exists():
        raise RuntimeError(
            f"Model with identifier {model_identifier} not found."
        )

    if model_version is None:
        return

    version_path = model_path / model_version
    if not version_path.exists():
        raise RuntimeError(
            f"Model version {model_version} "
            "for model {model_identifier} not found."
        )
