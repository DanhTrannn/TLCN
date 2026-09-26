#!/usr/bin/env python3
"""
Apache Polaris RBAC as Code Reconciler.

Reads a declarative YAML configuration file (rbac.yml) and idempotently
synchronizes Polaris catalogs, namespaces, catalog roles, principal roles,
privilege grants, and principals.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [polaris-rbac] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("polaris-rbac")

TOP_LEVEL_PRIVILEGES = {
    "CATALOG_MANAGE_CONTENT",
    "CATALOG_MANAGE_ACCESS",
    "CATALOG_MANAGE_METADATA",
    "CATALOG_READ_PROPERTIES",
    "TABLE_READ_DATA",
    "TABLE_WRITE_DATA",
    "TABLE_FULL_METADATA",
    "VIEW_FULL_METADATA",
    "NAMESPACE_FULL_METADATA",
}

SYSTEM_CATALOG_ROLES = {"catalog_admin"}
SYSTEM_PRINCIPAL_ROLES = {"service_admin"}
SYSTEM_PRINCIPALS = {"root"}


def expand_env(val: Any) -> Any:
    """Recursively expand environment variables formatted as ${VAR} or ${VAR:-default}."""
    if isinstance(val, str):
        pattern = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default_val = match.group(2) if match.group(2) is not None else ""
            return os.environ.get(var_name, default_val)

        return pattern.sub(replacer, val)
    elif isinstance(val, dict):
        return {k: expand_env(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [expand_env(item) for item in val]
    return val


class PolarisClient:
    """HTTP client for Apache Polaris REST and Management APIs."""

    def __init__(
        self,
        base_url: str,
        realm: str,
        root_client_id: str,
        root_client_secret: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.root_client_id = root_client_id
        self.root_client_secret = root_client_secret
        self.token: Optional[str] = None
        self.token_expiry: float = 0

    def obtain_token(self, client_id: str, client_secret: str) -> Optional[str]:
        """Obtain an OAuth2 token using client credentials."""
        token_url = f"{self.base_url}/api/catalog/v1/oauth/tokens"
        data = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "PRINCIPAL_ROLE:ALL",
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            token_url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("access_token")
        except Exception:
            return None

    def ensure_root_token(self, max_retries: int = 30, retry_delay: float = 2.0) -> str:
        """Ensure a valid root Bearer token is available, retrying if Polaris is starting."""
        now = time.time()
        if self.token and now < self.token_expiry - 60:
            return self.token

        for attempt in range(1, max_retries + 1):
            token = self.obtain_token(self.root_client_id, self.root_client_secret)
            if token:
                self.token = token
                self.token_expiry = time.time() + 3600
                logger.info("Successfully authenticated with Polaris as root.")
                return token
            logger.warning(
                "Waiting for Polaris root authentication (attempt %d/%d)...",
                attempt,
                max_retries,
            )
            time.sleep(retry_delay)

        raise RuntimeError("Failed to obtain root Bearer token from Polaris.")

    def request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        expected_statuses: Tuple[int, ...] = (200, 201, 204),
    ) -> Tuple[int, Any]:
        """Perform an authenticated request against Polaris Management API."""
        token = self.ensure_root_token()
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Polaris-Realm": self.realm,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                body = resp.read().decode("utf-8")
                res = json.loads(body) if body else None
                return status, res
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            res = None
            try:
                res = json.loads(body) if body else None
            except Exception:
                res = body
            if e.code in expected_statuses or e.code in (404, 409):
                return e.code, res
            logger.error("HTTP %s on %s %s: %s", e.code, method, path, body)
            raise


def load_saved_credentials(cred_file: Path) -> Dict[str, str]:
    """Parse existing credentials from the clients.env file."""
    if not cred_file.is_file() or cred_file.stat().st_size == 0:
        return {}
    creds: Dict[str, str] = {}
    for line in cred_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        creds[key] = val
    return creds


class PolarisRbacReconciler:
    """Orchestrates reconciliation of the Polaris RBAC model from config."""

    def __init__(self, client: PolarisClient, config: Dict[str, Any], cred_file: Path):
        self.client = client
        self.config = expand_env(config)
        self.cred_file = cred_file
        self.catalog_name: str = self.config["catalog"]["name"]
        self.saved_creds = load_saved_credentials(cred_file)
        self.output_creds: Dict[str, str] = dict(self.saved_creds)

    def reconcile_catalog(self) -> None:
        """Ensure catalog exists and has correct storage configuration."""
        cat_conf = self.config["catalog"]
        name = cat_conf["name"]
        s3 = cat_conf.get("s3", {})
        default_base = cat_conf.get(
            "default_base_location", f"s3://{name}/warehouse"
        )
        allowed_locations = cat_conf.get("allowed_locations", [f"s3://{name}/"])
        s3_endpoint = s3.get("endpoint", "http://minio:9000")
        s3_endpoint_internal = s3.get("endpoint_internal", "http://minio:9000")
        region = s3.get("region", "us-east-1")

        status, res = self.client.request(
            "GET", f"/api/management/v1/catalogs/{name}", expected_statuses=(200, 404)
        )

        catalog_data = {
            "name": name,
            "type": "INTERNAL",
            "readOnly": False,
            "properties": {"default-base-location": default_base},
            "storageConfigInfo": {
                "storageType": "S3",
                "allowedLocations": allowed_locations,
                "endpoint": s3_endpoint,
                "endpointInternal": s3_endpoint_internal,
                "pathStyleAccess": True,
                "region": region,
            },
        }

        if status == 404:
            logger.info("Catalog '%s' does not exist. Creating...", name)
            self.client.request(
                "POST",
                "/api/management/v1/catalogs",
                payload={"catalog": catalog_data},
            )
            logger.info("Catalog '%s' created successfully.", name)
        else:
            entity_version = res.get("entityVersion", 1)
            update_payload = {
                "currentEntityVersion": entity_version,
                "properties": {"default-base-location": default_base},
                "storageConfigInfo": catalog_data["storageConfigInfo"],
            }
            self.client.request(
                "PUT",
                f"/api/management/v1/catalogs/{name}",
                payload=update_payload,
            )
            logger.info("Catalog '%s' configuration verified and updated.", name)

    def purge_unmanaged_entities(self) -> None:
        """Purge principals and roles that are not listed in rbac.yml (except system ones)."""
        purge_principals = self.config.get("purge_unmanaged_principals", False)
        purge_roles = self.config.get("purge_unmanaged_roles", False)

        if purge_principals:
            managed_principals: Set[str] = set(self.config.get("principals", {}).keys())
            status, res = self.client.request("GET", "/api/management/v1/principals")
            if status == 200 and res:
                for p in res.get("principals", []):
                    p_name = p.get("name")
                    if p_name and p_name not in SYSTEM_PRINCIPALS and p_name not in managed_principals:
                        logger.warning("Purging unmanaged principal: '%s'", p_name)
                        self.client.request(
                            "DELETE",
                            f"/api/management/v1/principals/{p_name}",
                            expected_statuses=(200, 204, 404),
                        )

        if purge_roles:
            # Purge unmanaged principal roles
            managed_p_roles: Set[str] = set(self.config.get("principal_roles", {}).keys())
            status, res = self.client.request("GET", "/api/management/v1/principal-roles")
            if status == 200 and res:
                for r in res.get("roles", []):
                    r_name = r.get("name")
                    if r_name and r_name not in SYSTEM_PRINCIPAL_ROLES and r_name not in managed_p_roles:
                        logger.warning("Purging unmanaged principal role: '%s'", r_name)
                        self.client.request(
                            "DELETE",
                            f"/api/management/v1/principal-roles/{r_name}",
                            expected_statuses=(200, 204, 404),
                        )

            # Purge unmanaged catalog roles
            managed_c_roles: Set[str] = set(self.config.get("catalog_roles", {}).keys())
            status, res = self.client.request(
                "GET", f"/api/management/v1/catalogs/{self.catalog_name}/catalog-roles"
            )
            if status == 200 and res:
                for r in res.get("roles", []):
                    r_name = r.get("name")
                    if r_name and r_name not in SYSTEM_CATALOG_ROLES and r_name not in managed_c_roles:
                        logger.warning("Purging unmanaged catalog role: '%s'", r_name)
                        self.client.request(
                            "DELETE",
                            f"/api/management/v1/catalogs/{self.catalog_name}/catalog-roles/{r_name}",
                            expected_statuses=(200, 204, 404),
                        )

    def reconcile_catalog_roles(self) -> None:
        """Ensure catalog roles exist and have the configured privilege grants."""
        target_roles: Dict[str, Any] = self.config.get("catalog_roles", {})

        for role_name, role_def in target_roles.items():
            status, _ = self.client.request(
                "GET",
                f"/api/management/v1/catalogs/{self.catalog_name}/catalog-roles/{role_name}",
                expected_statuses=(200, 404),
            )
            if status == 404:
                logger.info(
                    "Creating catalog role '%s' in catalog '%s'...",
                    role_name,
                    self.catalog_name,
                )
                self.client.request(
                    "POST",
                    f"/api/management/v1/catalogs/{self.catalog_name}/catalog-roles",
                    payload={"catalogRole": {"name": role_name, "properties": {}}},
                    expected_statuses=(200, 201, 409),
                )

            # Reconcile privilege grants
            _, grants_res = self.client.request(
                "GET",
                f"/api/management/v1/catalogs/{self.catalog_name}/catalog-roles/{role_name}/grants",
            )
            existing_grants = {
                g.get("privilege")
                for g in (grants_res.get("grants", []) if grants_res else [])
                if g.get("privilege")
            }

            configured_grants: List[Dict[str, str]] = role_def.get("grants", [])
            target_privileges = {
                g.get("privilege") for g in configured_grants if g.get("privilege")
            }

            # Add missing privileges
            for grant in configured_grants:
                priv = grant.get("privilege")
                if priv and priv not in existing_grants:
                    logger.info(
                        "Granting privilege '%s' to catalog role '%s'...",
                        priv,
                        role_name,
                    )
                    self.client.request(
                        "PUT",
                        f"/api/management/v1/catalogs/{self.catalog_name}/catalog-roles/{role_name}/grants",
                        payload={"type": grant.get("type", "catalog"), "privilege": priv},
                        expected_statuses=(200, 201, 409),
                    )

            # Revoke unconfigured top-level privileges if prune requested
            if self.config.get("prune_unmanaged_privileges", False):
                for priv in (existing_grants & TOP_LEVEL_PRIVILEGES) - target_privileges:
                    logger.info(
                        "Revoking privilege '%s' from catalog role '%s'...",
                        priv,
                        role_name,
                    )
                    self.client.request(
                        "POST",
                        f"/api/management/v1/catalogs/{self.catalog_name}/catalog-roles/{role_name}/grants",
                        payload={"grant": {"type": "catalog", "privilege": priv}},
                        expected_statuses=(200, 201, 204),
                    )

    def reconcile_principal_roles(self) -> None:
        """Ensure principal roles exist and inherit the assigned catalog roles."""
        target_roles: Dict[str, Any] = self.config.get("principal_roles", {})

        for role_name, role_def in target_roles.items():
            status, _ = self.client.request(
                "GET",
                f"/api/management/v1/principal-roles/{role_name}",
                expected_statuses=(200, 404),
            )
            if status == 404:
                logger.info("Creating principal role '%s'...", role_name)
                self.client.request(
                    "POST",
                    "/api/management/v1/principal-roles",
                    payload={"principalRole": {"name": role_name, "properties": {}}},
                    expected_statuses=(200, 201, 409),
                )

            # Assigned catalog roles
            _, cat_roles_res = self.client.request(
                "GET",
                f"/api/management/v1/principal-roles/{role_name}/catalog-roles/{self.catalog_name}",
            )
            assigned_roles = {
                r.get("name")
                for r in (cat_roles_res.get("roles", []) if cat_roles_res else [])
                if r.get("name")
            }

            configured_cat_roles: Set[str] = set(role_def.get("catalog_roles", []))

            # Add missing catalog roles
            for cr in configured_cat_roles - assigned_roles:
                logger.info(
                    "Binding catalog role '%s' to principal role '%s'...",
                    cr,
                    role_name,
                )
                self.client.request(
                    "PUT",
                    f"/api/management/v1/principal-roles/{role_name}/catalog-roles/{self.catalog_name}",
                    payload={"catalogRole": {"name": cr}},
                    expected_statuses=(200, 201, 409),
                )

            # Revoke removed catalog roles
            for cr in assigned_roles - configured_cat_roles:
                logger.info(
                    "Revoking catalog role '%s' from principal role '%s'...",
                    cr,
                    role_name,
                )
                self.client.request(
                    "DELETE",
                    f"/api/management/v1/principal-roles/{role_name}/catalog-roles/{self.catalog_name}/{cr}",
                    expected_statuses=(200, 204, 404),
                )

    def reconcile_principals(self) -> None:
        """Ensure principals exist, have valid credentials, and principal roles assigned."""
        target_principals: Dict[str, Any] = self.config.get("principals", {})

        for principal_name, p_def in target_principals.items():
            export_spec = p_def.get("credentials_export", {})
            id_var = export_spec.get("client_id_var")
            secret_var = export_spec.get("client_secret_var")

            # Check if saved credentials are still valid
            saved_id = self.saved_creds.get(id_var) if id_var else None
            saved_secret = self.saved_creds.get(secret_var) if secret_var else None

            creds_valid = False
            if saved_id and saved_secret:
                test_token = self.client.obtain_token(saved_id, saved_secret)
                if test_token:
                    creds_valid = True
                    logger.info("Reusing valid credentials for principal '%s'.", principal_name)

            client_id = saved_id
            client_secret = saved_secret

            if not creds_valid:
                # Check if principal exists
                status, _ = self.client.request(
                    "GET",
                    f"/api/management/v1/principals/{principal_name}",
                    expected_statuses=(200, 404),
                )

                if status == 404:
                    logger.info("Creating principal '%s'...", principal_name)
                    _, create_res = self.client.request(
                        "POST",
                        "/api/management/v1/principals",
                        payload={
                            "principal": {
                                "name": principal_name,
                                "properties": {"service": self.catalog_name},
                            },
                            "credentialRotationRequired": False,
                        },
                    )
                    creds = (create_res or {}).get("credentials", {})
                    client_id = creds.get("clientId")
                    client_secret = creds.get("clientSecret")
                else:
                    logger.info("Rotating/resetting credentials for '%s'...", principal_name)
                    _, reset_res = self.client.request(
                        "POST",
                        f"/api/management/v1/principals/{principal_name}/reset",
                        payload={},
                    )
                    creds = (reset_res or {}).get("credentials", {})
                    client_id = creds.get("clientId")
                    client_secret = creds.get("clientSecret")

                if not client_id or not client_secret:
                    raise RuntimeError(
                        f"Failed to obtain credentials for principal '{principal_name}'"
                    )

            if id_var and client_id:
                self.output_creds[id_var] = client_id
            if secret_var and client_secret:
                self.output_creds[secret_var] = client_secret

            # Reconcile principal roles
            _, p_roles_res = self.client.request(
                "GET",
                f"/api/management/v1/principals/{principal_name}/principal-roles",
            )
            assigned_p_roles = {
                r.get("name")
                for r in (p_roles_res.get("roles", []) if p_roles_res else [])
                if r.get("name")
            }

            configured_p_roles: Set[str] = set(p_def.get("principal_roles", []))

            for pr in configured_p_roles - assigned_p_roles:
                logger.info(
                    "Assigning principal role '%s' to principal '%s'...",
                    pr,
                    principal_name,
                )
                self.client.request(
                    "PUT",
                    f"/api/management/v1/principals/{principal_name}/principal-roles",
                    payload={"principalRole": {"name": pr}},
                    expected_statuses=(200, 201, 409),
                )

            for pr in assigned_p_roles - configured_p_roles:
                logger.info(
                    "Revoking principal role '%s' from principal '%s'...",
                    pr,
                    principal_name,
                )
                self.client.request(
                    "DELETE",
                    f"/api/management/v1/principals/{principal_name}/principal-roles/{pr}",
                    expected_statuses=(200, 204, 404),
                )

    def write_credential_file(self) -> None:
        """Write out clients.env containing exported principal credentials."""
        managed_keys: Set[str] = set()
        for p_def in self.config.get("principals", {}).values():
            export_spec = p_def.get("credentials_export", {})
            if export_spec.get("client_id_var"):
                managed_keys.add(export_spec["client_id_var"])
            if export_spec.get("client_secret_var"):
                managed_keys.add(export_spec["client_secret_var"])

        self.cred_file.parent.mkdir(parents=True, exist_ok=True)
        content_lines = [
            f"# Generated automatically by sync_polaris_rbac.py at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        ]
        for key in sorted(self.output_creds.keys()):
            if key in managed_keys:
                val = self.output_creds[key]
                content_lines.append(f"{key}='{val}'")
        content_lines.append("")

        tmp_file = self.cred_file.with_suffix(".tmp")
        tmp_file.write_text("\n".join(content_lines), encoding="utf-8")
        os.chmod(tmp_file, 0o644)
        tmp_file.replace(self.cred_file)
        logger.info("Saved credentials to '%s'.", self.cred_file)

    def reconcile_namespaces(self) -> None:
        """Ensure all required namespaces exist in the catalog."""
        target_namespaces: List[str] = self.config.get("namespaces", [])
        if not target_namespaces:
            return

        for ns in target_namespaces:
            status, _ = self.client.request(
                "POST",
                f"/api/catalog/v1/{self.catalog_name}/namespaces",
                payload={"namespace": [ns], "properties": {}},
                expected_statuses=(200, 201, 409),
            )
            if status in (200, 201):
                logger.info("Namespace '%s' created in catalog '%s'.", ns, self.catalog_name)
            else:
                logger.info("Namespace '%s' already exists.", ns)

    def reconcile(self) -> None:
        """Execute full reconciliation sequence."""
        logger.info("Starting Polaris RBAC reconciliation...")
        self.reconcile_catalog()
        self.purge_unmanaged_entities()
        self.reconcile_catalog_roles()
        self.reconcile_principal_roles()
        self.reconcile_principals()
        self.write_credential_file()
        self.reconcile_namespaces()
        logger.info("Polaris RBAC reconciliation completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize Apache Polaris RBAC from YAML")
    parser.add_argument(
        "--config",
        "-c",
        default=os.environ.get("POLARIS_RBAC_CONFIG", "/bootstrap/rbac.yml"),
        help="Path to rbac.yml configuration file",
    )
    parser.add_argument(
        "--polaris-url",
        default=os.environ.get("POLARIS_URL", "http://polaris:8181"),
        help="Base URL of Apache Polaris server",
    )
    parser.add_argument(
        "--realm",
        default=os.environ.get("POLARIS_REALM", "POLARIS"),
        help="Polaris realm name",
    )
    parser.add_argument(
        "--root-client-id",
        default=os.environ.get("POLARIS_ROOT_CLIENT_ID", "root"),
        help="Polaris root client ID",
    )
    parser.add_argument(
        "--root-client-secret",
        default=os.environ.get("POLARIS_ROOT_CLIENT_SECRET", "password"),
        help="Polaris root client secret",
    )
    parser.add_argument(
        "--credential-file",
        default=os.environ.get("POLARIS_CREDENTIAL_FILE", "/run/polaris/clients.env"),
        help="Path to output credentials file (clients.env)",
    )
    parser.add_argument(
        "--ready-file",
        default="/run/polaris/ready",
        help="Path to touched ready file",
    )

    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        # Fallback to local path if running outside container
        local_fallback = Path(__file__).parent / "rbac.yml"
        if local_fallback.is_file():
            config_path = local_fallback
        else:
            logger.error("Configuration file not found: %s", args.config)
            sys.exit(1)

    logger.info("Loading RBAC configuration from %s", config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    client = PolarisClient(
        base_url=args.polaris_url,
        realm=args.realm,
        root_client_id=args.root_client_id,
        root_client_secret=args.root_client_secret,
    )

    reconciler = PolarisRbacReconciler(
        client=client,
        config=config,
        cred_file=Path(args.credential_file),
    )

    reconciler.reconcile()

    ready_path = Path(args.ready_file)
    try:
        ready_path.parent.mkdir(parents=True, exist_ok=True)
        ready_path.touch()
    except Exception as e:
        logger.warning("Could not touch ready file %s: %s", ready_path, e)


if __name__ == "__main__":
    main()
