"""
Agent Streamer for IngeTrazo Agent Bridge (Port 8482)
Enables live streaming of .debim.yaml manifests directly to running IngeTrazo 3D viewport.
"""

from typing import Any, Dict, List, Optional, Union
import json
import urllib.error
import urllib.request
try:
    import yaml
    def _dump_yaml_str(data: Any) -> str:
        return yaml.dump(data, sort_keys=False, allow_unicode=True)
except ImportError:
    from chakkree_tools.exporter.pure_yaml import dump_yaml as _dump_yaml_str

from chakkree_tools.exporter.debim_exporter import DebimExporter


class AgentStreamerError(Exception):
    """Exception raised when streaming or probe check to IngeTrazo Agent Bridge fails."""
    pass


class AgentStreamer:
    """
    Client for streaming BIM models and manifests to IngeTrazo via Agent Bridge.
    Default bridge URL: http://127.0.0.1:8482
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8482,
        scheme: str = "http",
        timeout: float = 3.0,
    ) -> None:
        self.host = host
        self.port = port
        self.scheme = scheme
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        """Returns the base URL for the Agent Bridge server."""
        return f"{self.scheme}://{self.host}:{self.port}"

    def is_bridge_available(self, timeout: Optional[float] = None) -> bool:
        """
        Probes the Agent Bridge port to check if IngeTrazo listener is active.

        :param timeout: Optional override for probe request timeout in seconds.
        :return: True if bridge responds or port is open/listening, False otherwise.
        """
        req_timeout = timeout if timeout is not None else self.timeout
        url = f"{self.base_url}/"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                return resp.status in (200, 204, 404, 405)
        except urllib.error.HTTPError:
            # Server responded with HTTP status code (e.g. 404/405/400), meaning host/port is alive
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def stream_manifest(
        self,
        manifest: Union[str, Dict[str, Any]],
        path: str = "/api/v1/stream",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Sends .debim.yaml manifest via HTTP POST to IngeTrazo Agent Bridge.

        :param manifest: The manifest as a YAML string or Python dictionary payload.
        :param path: API endpoint path (default: /api/v1/stream or /).
        :param headers: Optional custom HTTP headers.
        :return: Parsed response dict or status details.
        """
        if isinstance(manifest, dict):
            payload_yaml = _dump_yaml_str(manifest)
        elif isinstance(manifest, str):
            payload_yaml = manifest
        else:
            raise ValueError("Manifest must be a dict or YAML string.")

        endpoint_url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        req_headers = {
            "Content-Type": "application/x-yaml",
            "Accept": "application/json, text/plain, */*",
        }
        if headers:
            req_headers.update(headers)

        data_bytes = payload_yaml.encode("utf-8")
        req = urllib.request.Request(
            endpoint_url,
            data=data_bytes,
            headers=req_headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_body = resp.read().decode("utf-8")
                status_code = resp.status
                try:
                    res_json = json.loads(resp_body) if resp_body else {}
                except json.JSONDecodeError:
                    res_json = {"raw_response": resp_body}

                return {
                    "status_code": status_code,
                    "success": 200 <= status_code < 300,
                    "response": res_json,
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            raise AgentStreamerError(
                f"HTTP {e.code} Error streaming to {endpoint_url}: {e.reason}. Detail: {err_body}"
            ) from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise AgentStreamerError(
                f"Failed to connect to IngeTrazo Agent Bridge at {endpoint_url}: {e}"
            ) from e

    def stream_elements(
        self,
        elements: List[Any],
        project_name: str = "Live Streamed Model",
        grids_x: Optional[Dict[str, float]] = None,
        grids_y: Optional[Dict[str, float]] = None,
        path: str = "/api/v1/stream",
        include_rebar_mesh: bool = False,
    ) -> Dict[str, Any]:
        """
        Convenience method to convert a list of RC elements directly to .debim manifest
        and stream it live into IngeTrazo.
        """
        exporter = DebimExporter(project_name=project_name)
        if grids_x and grids_y:
            exporter.set_grids(grids_x, grids_y)
        for elem in elements:
            exporter.add_element(elem)

        manifest_dict = exporter.to_dict(include_rebar_mesh=include_rebar_mesh)
        return self.stream_manifest(manifest=manifest_dict, path=path)


def stream_to_ingetrazo(
    elements_or_manifest: Union[List[Any], Dict[str, Any], str],
    host: str = "127.0.0.1",
    port: int = 8482,
    include_rebar_mesh: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function for live streaming models to IngeTrazo.
    """
    streamer = AgentStreamer(host=host, port=port)
    if isinstance(elements_or_manifest, list):
        return streamer.stream_elements(elements_or_manifest, include_rebar_mesh=include_rebar_mesh)
    else:
        return streamer.stream_manifest(elements_or_manifest)
