"""Kubernetes API client abstraction for Aegis Sentinel."""

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.settings import Settings
from src.errors.exceptions import InfrastructureError
from src.logger.logger import get_logger

logger = get_logger("kubernetes.client")


class BaseKubeClient:
    """Base interface for Kubernetes API access."""

    def is_connected(self) -> bool:
        raise NotImplementedError

    def get_deployment(self, name: str, namespace: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def list_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_pod(self, name: str, namespace: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def list_events(self, namespace: Optional[str] = None, field_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def list_nodes(self) -> List[Dict[str, Any]]:
        raise NotImplementedError


class KubernetesClient(BaseKubeClient):
    """
    Standard Kubernetes API client supporting in-cluster ServiceAccount
    and local kubeconfig API discovery.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.namespace = settings.kubernetes_namespace or "default"
        self.api_server: Optional[str] = None
        self.token: Optional[str] = None
        self.ca_cert: Optional[str] = None
        self.is_configured = False
        self._discover_configuration()

    def _discover_configuration(self) -> None:
        """Discover in-cluster or kubeconfig credentials."""
        # 1. In-cluster ServiceAccount
        sa_token_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
        sa_ca_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
        sa_ns_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")

        if sa_token_path.is_file() and sa_ca_path.is_file():
            try:
                self.token = sa_token_path.read_text().strip()
                self.ca_cert = str(sa_ca_path)
                self.api_server = "https://kubernetes.default.svc"
                if sa_ns_path.is_file() and not self.settings.kubernetes_namespace:
                    self.namespace = sa_ns_path.read_text().strip()
                self.is_configured = True
                logger.info(f"Initialized in-cluster Kubernetes configuration (namespace={self.namespace})")
                return
            except Exception as e:
                logger.warning(f"Failed loading in-cluster ServiceAccount credentials: {e}")

        # 2. Local Kubeconfig discovery (from ~/.kube/config or KUBECONFIG env)
        kubeconfig_path_str = os.getenv("KUBECONFIG", str(Path.home() / ".kube" / "config"))
        kubeconfig_path = Path(kubeconfig_path_str)

        if kubeconfig_path.is_file():
            try:
                self._parse_simple_kubeconfig(kubeconfig_path)
                self.is_configured = True
                logger.info(f"Loaded Kubernetes configuration from {kubeconfig_path} (server={self.api_server})")
                return
            except Exception as e:
                logger.debug(f"Could not initialize from kubeconfig: {e}")

        logger.debug("No active Kubernetes cluster configuration discovered.")

    def _parse_simple_kubeconfig(self, path: Path) -> None:
        """Lightweight parser for basic kubeconfig cluster endpoint."""
        # Simple YAML extraction for server endpoint without heavy external dependencies
        content = path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("server:"):
                server_url = line.partition("server:")[2].strip().strip("'\"")
                if server_url:
                    self.api_server = server_url
                    break

    def is_connected(self) -> bool:
        """Check if Kubernetes API is reachable."""
        if not self.is_configured or not self.api_server:
            return False
        try:
            self._request("/version", timeout=3)
            return True
        except Exception:
            return False

    def _request(self, path: str, timeout: int = 10) -> Dict[str, Any]:
        """Perform authenticated HTTPS request to kube-apiserver."""
        if not self.api_server:
            raise InfrastructureError(
                "Kubernetes API server is not configured. Cluster connection unavailable.",
                details={"configured": False},
            )

        url = f"{self.api_server.rstrip('/')}{path}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "aegis-sentinel/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        ctx = ssl.create_default_context()
        if self.ca_cert and os.path.exists(self.ca_cert):
            ctx.load_verify_locations(self.ca_cert)
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except urllib.error.HTTPError as he:
            if he.code == 404:
                return {}
            error_body = he.read().decode("utf-8", errors="ignore")
            raise InfrastructureError(
                f"Kubernetes API returned HTTP {he.code}: {error_body}",
                details={"status_code": he.code, "path": path},
            ) from he
        except Exception as e:
            raise InfrastructureError(
                f"Failed connecting to Kubernetes API ({url}): {e}",
                details={"api_server": self.api_server, "path": path},
            ) from e

    def get_deployment(self, name: str, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns = namespace or self.namespace
        res = self._request(f"/apis/apps/v1/namespaces/{ns}/deployments/{name}")
        return res if res.get("kind") == "Deployment" else None

    def list_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        ns = namespace or self.namespace
        query = f"?labelSelector={label_selector}" if label_selector else ""
        res = self._request(f"/api/v1/namespaces/{ns}/pods{query}")
        return res.get("items", [])

    def get_pod(self, name: str, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns = namespace or self.namespace
        res = self._request(f"/api/v1/namespaces/{ns}/pods/{name}")
        return res if res.get("kind") == "Pod" else None

    def list_events(self, namespace: Optional[str] = None, field_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        ns = namespace or self.namespace
        query = f"?fieldSelector={field_selector}" if field_selector else ""
        res = self._request(f"/api/v1/namespaces/{ns}/events{query}")
        return res.get("items", [])

    def list_nodes(self) -> List[Dict[str, Any]]:
        res = self._request("/api/v1/nodes")
        return res.get("items", [])


class MockKubernetesClient(BaseKubeClient):
    """Mock Kubernetes client for unit testing without live cluster."""

    def __init__(
        self,
        deployments: Optional[List[Dict[str, Any]]] = None,
        pods: Optional[List[Dict[str, Any]]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        connected: bool = True,
    ) -> None:
        self.deployments = {d.get("metadata", {}).get("name"): d for d in (deployments or [])}
        self.pods = pods or []
        self.events = events or []
        self.nodes = nodes or []
        self._connected = connected

    def is_connected(self) -> bool:
        return self._connected

    def get_deployment(self, name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        if not self._connected:
            raise InfrastructureError("Cluster connection unavailable")
        return self.deployments.get(name)

    def list_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self._connected:
            raise InfrastructureError("Cluster connection unavailable")
        return [
            p for p in self.pods
            if (namespace is None or p.get("metadata", {}).get("namespace") == namespace)
        ]

    def get_pod(self, name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        if not self._connected:
            raise InfrastructureError("Cluster connection unavailable")
        for p in self.pods:
            if p.get("metadata", {}).get("name") == name:
                return p
        return None

    def list_events(self, namespace: Optional[str] = None, field_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self._connected:
            raise InfrastructureError("Cluster connection unavailable")
        return [
            e for e in self.events
            if (namespace is None or e.get("metadata", {}).get("namespace") == namespace)
        ]

    def list_nodes(self) -> List[Dict[str, Any]]:
        if not self._connected:
            raise InfrastructureError("Cluster connection unavailable")
        return self.nodes

