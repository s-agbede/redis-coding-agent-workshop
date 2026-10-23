# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML>=6.0.2,<7"]
# ///
"""Validate a local portal project; optionally build and check it with Docker."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any
import re
import subprocess
import sys
import time
import tempfile
import urllib.error
import urllib.request
import uuid


class ProjectError(ValueError):
    """An actionable project validation or readiness failure."""


@dataclass(frozen=True)
class Project:
    root: Path
    context: Path
    dockerfile: Path
    port: int
    health_path: str
    required_env: tuple[str, ...]
    runtime_type: str = "docker"
    compose_file: Path | None = None
    service: str = ""


def checked_text(value: object, name: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.encode("utf-16-le", errors="surrogatepass")) // 2 > maximum
        or re.search(r"[\x00-\x1f\x7f]", value)
    ):
        raise ProjectError(f"{name} must contain 1–{maximum} characters without controls.")
    return value.strip()


def contained_path(
    root: Path, base: Path, value: object, allow_root: bool = False,
) -> Path:
    if allow_root and value in ("", "."):
        return base
    path = checked_text(value, "Build path", 512)
    if any(char in path for char in "\\%") or any(
        part in ("", ".", "..") for part in path.split("/")
    ):
        raise ProjectError("Build paths must be relative paths inside the project.")
    candidate = base / path
    for segment in (candidate, *candidate.parents):
        if segment == root:
            break
        if segment.is_symlink():
            raise ProjectError("Project paths cannot contain symlinks.")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ProjectError("Build paths must stay inside the project.")
    return resolved


def read_project_file(path: Path) -> str:
    try:
        if not path.is_file() or path.stat().st_size > 128 * 1024:
            raise ProjectError(f"{path.name} must be a regular text file up to 128 KiB.")
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ProjectError(f"Cannot read {path.name} as UTF-8 text.") from error
    if not text.strip() or "\x00" in text:
        raise ProjectError(f"{path.name} must contain nonempty text without NUL bytes.")
    return text


def check_project(directory: Path) -> Project:
    root = directory.resolve()
    manifest_text = read_project_file(contained_path(root, root, "portal-project.json"))
    try:
        data = json.loads(manifest_text)
    except json.JSONDecodeError as error:
        raise ProjectError("Provide valid JSON in portal-project.json.") from error
    allowed = {"version", "kind", "title", "description", "runtime", "requiredEnv"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ProjectError("Use only the documented manifest fields.")
    if type(data.get("version")) not in (int, float) or data["version"] != 1:
        raise ProjectError("Manifest version must be 1.")
    read_project_file(contained_path(root, root, "README.md"))
    if data.get("kind") not in ("demo", "workshop"):
        raise ProjectError("kind must be demo or workshop.")
    checked_text(data.get("title"), "title", 120)
    checked_text(data.get("description"), "description", 1000)
    runtime = data.get("runtime")
    if not isinstance(runtime, dict):
        raise ProjectError("Provide runtime settings.")
    runtime_type = runtime.get("type", "docker")
    if runtime_type not in ("docker", "compose"):
        raise ProjectError("runtime.type must be docker or compose.")
    fields = {"type", "port", "healthPath"}
    fields |= {"context", "dockerfile"} if runtime_type == "docker" else {"file", "service"}
    if set(runtime) - fields:
        raise ProjectError("Use only the documented runtime settings.")
    context, dockerfile = root, root / "Dockerfile"
    compose_file, service = None, ""
    if runtime_type == "docker":
        context = contained_path(root, root, runtime.get("context"), allow_root=True)
        dockerfile = contained_path(root, context, runtime.get("dockerfile"))
        if not context.is_dir():
            raise ProjectError("Build context must be a directory.")
        read_project_file(dockerfile)
    else:
        compose_file = contained_path(root, root, runtime.get("file"))
        read_project_file(compose_file)
        service = checked_text(runtime.get("service"), "service", 128)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", service):
            raise ProjectError("Use a valid Compose service name.")
    port = runtime.get("port")
    if type(port) not in (int, float) or not 1 <= port <= 65535 or port % 1:
        raise ProjectError("runtime.port must be an integer from 1 to 65535.")
    health = checked_text(runtime.get("healthPath"), "healthPath", 256)
    if (
        not health.startswith("/")
        or health.startswith("//")
        or re.search(r"[\\%?#\s]", health)
        or any(part in (".", "..") for part in health.split("/"))
    ):
        raise ProjectError("healthPath must be a local absolute URL path, for example /health.")
    names = data.get("requiredEnv")
    if (
        not isinstance(names, list)
        or len(names) > 50
        or any(
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", name)
            for name in names
        )
        or len(names) != len(set(names))
    ):
        raise ProjectError("requiredEnv must list up to 50 unique variable names, not values.")
    project = Project(
        root, context, dockerfile, int(port), health, tuple(names),
        runtime_type, compose_file, service,
    )
    if runtime_type == "compose":
        read_compose_profile(project)
    return project


def docker(arguments: list[str], timeout: float = 120, check: bool = True) -> str:
    # Suppress build/application output: it may contain credentials from user code.
    result = subprocess.run(
        ["docker", *arguments], capture_output=True, text=True,
        timeout=timeout, check=check,
    )
    absent = any(message in result.stderr for message in ("No such container:", "No such image:"))
    if not check and result.returncode and not absent:
        raise subprocess.CalledProcessError(result.returncode, ["docker", *arguments])
    return result.stdout.strip()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: urllib.request.Request, fp: object, code: int,
        msg: str, headers: object, newurl: str,
    ) -> None:
        return None


def wait_ready(url: str, timeout: float) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with opener.open(url, timeout=min(2, max(0.1, deadline - time.monotonic()))) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            pass  # The service may still be starting; the deadline is the failure boundary.
        time.sleep(min(0.2, max(0, deadline - time.monotonic())))
    raise ProjectError("Readiness timed out: the health endpoint did not return HTTP 200.")




def read_compose_profile(project: Project) -> dict[str, Any]:
    """Reject unsupported raw YAML before Compose can resolve other files."""
    try:
        import yaml
    except ImportError as error:
        raise ProjectError("Compose checking needs PyYAML. Run: uv run check_project.py . --run") from error
    try:
        source = read_project_file(project.compose_file)
        for token in yaml.scan(source):
            if isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)):
                raise ProjectError("Compose aliases and anchors are unsupported in portable profiles.")
        class UniqueLoader(yaml.SafeLoader):
            pass

        def unique_mapping(loader: Any, node: Any, deep: bool = False) -> dict[str, Any]:
            mapping: dict[str, Any] = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=deep)
                if not isinstance(key, str) or key in mapping:
                    raise ProjectError("Compose mappings require unique string keys.")
                mapping[key] = loader.construct_object(value_node, deep=deep)
            return mapping

        UniqueLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping,
        )
        config = yaml.load(source, Loader=UniqueLoader)
    except (yaml.YAMLError, RecursionError) as error:
        raise ProjectError("Provide valid Compose YAML without custom tags.") from error
    nodes = 0

    def check_depth(value: Any, depth: int = 0) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > 10000 or depth > 40:
            raise ProjectError("Compose document is too complex for the portable profile.")
        children = value.values() if isinstance(value, dict) else value if isinstance(value, list) else []
        for child in children:
            check_depth(child, depth + 1)

    check_depth(config)
    if not isinstance(config, dict) or set(config) - {"services", "volumes", "networks"}:
        raise ProjectError("Portable Compose supports services, volumes and networks only.")
    services = config.get("services")
    if not isinstance(services, dict) or not 1 <= len(services) <= 10 or project.service not in services:
        raise ProjectError("Provide 1–10 services including the entry service.")
    for resource in ("volumes", "networks"):
        resources = config.get(resource, {})
        if not isinstance(resources, dict) or len(resources) > 20:
            raise ProjectError(f"Compose {resource} must be named mappings.")
        for name, settings in resources.items():
            if not isinstance(name, str) or len(name) > 128 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
                raise ProjectError("Use literal project resource names.")
            if settings not in (None, {}):
                raise ProjectError("Use default project-owned volumes and networks without custom names or drivers.")
    allowed = {
        "build", "image", "command", "entrypoint", "environment", "healthcheck",
        "depends_on", "volumes", "networks", "expose", "restart", "working_dir",
        "user", "init", "stop_grace_period", "read_only", "tmpfs",
    }
    for name, service in services.items():
        if not isinstance(name, str) or len(name) > 128 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ProjectError("Use literal Compose service names.")
        if not isinstance(service, dict) or set(service) - allowed:
            raise ProjectError(f"Service {name} uses unsupported settings or published ports.")
        build = service.get("build")
        if isinstance(build, str):
            build = {"context": build}
        if build is not None:
            if not isinstance(build, dict) or set(build) - {"context", "dockerfile", "args", "target"}:
                raise ProjectError("Builds support local context, Dockerfile, args and target only.")
            context_value = build.get("context", ".")
            dockerfile_value = build.get("dockerfile", "Dockerfile")
            if context_value == "" or "$" in str(context_value) or "$" in str(dockerfile_value):
                raise ProjectError("Build paths cannot contain environment interpolation.")
            context = contained_path(project.root, project.compose_file.parent, context_value, allow_root=True)
            read_project_file(contained_path(project.root, context, dockerfile_value))
        image = service.get("image")
        if image is not None and (not isinstance(image, str) or "$" in image):
            raise ProjectError("Use literal image references without environment interpolation.")
        mounts = service.get("volumes", [])
        if not isinstance(mounts, list) or len(mounts) > 20:
            raise ProjectError("Service volumes must be a list of named mounts.")
        for mount in mounts:
            if isinstance(mount, str):
                parts = mount.split(":")
                if len(parts) not in (2, 3) or (len(parts) == 3 and parts[2] not in ("ro", "rw")):
                    raise ProjectError("Use named volume mounts only.")
                source, target = parts[:2]
            elif isinstance(mount, dict):
                if mount.get("type") != "volume" or set(mount) - {"type", "source", "target", "read_only"}:
                    raise ProjectError("Use named volume mounts only.")
                if "read_only" in mount and not isinstance(mount["read_only"], bool):
                    raise ProjectError("Volume read_only must be a boolean.")
                source, target = mount.get("source"), mount.get("target")
            else:
                raise ProjectError("Use named volume mounts only.")
            if (
                not isinstance(source, str) or source not in config.get("volumes", {})
                or not isinstance(target, str) or not target.startswith("/")
                or re.search(r"[$\\\x00-\x1f]", target) or ".." in target.split("/")
            ):
                raise ProjectError("Mounts must reference declared named volumes and absolute container paths.")
        for field, available in (("networks", config.get("networks", {})), ("depends_on", services)):
            references = service.get(field, [])
            if not isinstance(references, (list, dict)):
                raise ProjectError(f"Service {field} must name declared resources.")
            if any(not isinstance(item, str) or item not in available for item in references):
                raise ProjectError(f"Service {field} must name declared resources.")
            if field == "networks" and isinstance(references, dict):
                if any(value not in (None, {}) for value in references.values()):
                    raise ProjectError("Service networks cannot override network configuration.")
    return config


def normalize_compose(project: Project, directory: Path, identifier: str) -> Path:
    """Resolve a deliberately small, portable Compose subset before execution."""
    read_compose_profile(project)
    empty_env = directory / "empty.env"
    empty_env.write_text("")
    arguments = [
        "compose", "--env-file", str(empty_env), "--project-directory", str(project.compose_file.parent),
        "-f", str(project.compose_file), "config", "--format", "json",
    ]
    try:
        config = json.loads(docker(arguments))
    except json.JSONDecodeError as error:
        raise ProjectError("Docker Compose returned invalid configuration.") from error
    if not isinstance(config, dict) or set(config) - {"name", "services", "volumes", "networks"}:
        raise ProjectError("Compose supports only services, volumes and networks.")
    services = config.get("services")
    if not isinstance(services, dict) or project.service not in services:
        raise ProjectError("The entry service must exist in the Compose configuration.")
    allowed_service = {
        "build", "image", "command", "entrypoint", "environment", "healthcheck",
        "depends_on", "volumes", "networks", "expose", "restart", "working_dir",
        "user", "init", "stop_grace_period", "labels", "read_only", "tmpfs",
    }
    volumes = config.get("volumes", {})
    networks = config.get("networks", {})
    for category, resources in (("volume", volumes), ("network", networks)):
        if not isinstance(resources, dict) or len(resources) > 20:
            raise ProjectError(f"Invalid Compose {category} definitions.")
        for name, settings in resources.items():
            settings = settings or {}
            # Compose generates names during normalization. Only its project-derived
            # default is accepted; explicit shared names must never be destroyed.
            generated = f"{config.get('name', '')}_{name}"
            # Compose emits an empty IPAM object even for an ordinary default network.
            if category == "network" and settings.get("ipam") == {}:
                settings.pop("ipam")
            if set(settings) - {"name", "labels"} or settings.get("name", generated) != generated:
                raise ProjectError(f"Compose {category}s must be project-owned defaults.")
            settings.pop("name", None)
            resources[name] = settings
    for name, service in services.items():
        if not isinstance(service, dict) or set(service) - allowed_service:
            raise ProjectError(f"Service {name} uses unsupported settings; omit published ports and host features.")
        build = service.get("build")
        if build is not None:
            if not isinstance(build, dict) or set(build) - {"context", "dockerfile", "args", "target"}:
                raise ProjectError("Builds support local context, Dockerfile, args and target only.")
            context = Path(build.get("context", ""))
            if not context.is_absolute():
                context = project.compose_file.parent / context
            try:
                relative = context.relative_to(project.root)
            except ValueError as error:
                raise ProjectError("Compose build contexts must stay inside the project.") from error
            safe_context = contained_path(project.root, project.root, str(relative), allow_root=True)
            dockerfile = contained_path(project.root, safe_context, build.get("dockerfile", "Dockerfile"))
            read_project_file(dockerfile)
            build["context"] = str(safe_context)
            service["image"] = f"{identifier}-{name}:check"
        elif not isinstance(service.get("image"), str) or not service["image"]:
            raise ProjectError(f"Service {name} requires a local build or image.")
        mounts = service.get("volumes", [])
        if not isinstance(mounts, list) or len(mounts) > 20:
            raise ProjectError("Service volumes must be a list of named mounts.")
        for mount in mounts:
            if (
                not isinstance(mount, dict)
                or mount.get("type") != "volume"
                or mount.get("source") not in volumes
                or set(mount) - {"type", "source", "target", "read_only", "volume"}
                or mount.get("volume", {})
            ):
                raise ProjectError("Use declared named volumes only; host mounts are unsupported.")
    services[project.service]["ports"] = [{
        "target": project.port, "published": "0", "host_ip": "127.0.0.1", "protocol": "tcp",
    }]
    config.pop("name", None)
    output = directory / "compose.json"
    def escape_interpolation(value: Any) -> Any:
        if isinstance(value, str):
            return value.replace("$", "$$")
        if isinstance(value, list):
            return [escape_interpolation(item) for item in value]
        if isinstance(value, dict):
            return {key: escape_interpolation(item) for key, item in value.items()}
        return value

    output.write_text(json.dumps(escape_interpolation(config)))
    output.chmod(0o600)
    return output


def run_compose(project: Project, timeout: float) -> None:
    identifier = "portal-check-" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="portal-check-") as temporary:
        directory = Path(temporary)
        resolved = normalize_compose(project, directory, identifier)
        command = [
            "compose", "--env-file", str(directory / "empty.env"),
            "--project-name", identifier, "-f", str(resolved),
        ]
        try:
            docker([*command, "build"], timeout=600)
            docker([*command, "up", "--detach", "--wait", "--wait-timeout", str(int(timeout))], timeout=timeout + 10)
            address = docker([*command, "port", project.service, str(project.port)])
            if not re.fullmatch(r"127\.0\.0\.1:[0-9]+", address):
                raise ProjectError("Compose did not return a loopback-only entry port.")
            wait_ready(f"http://{address}{project.health_path}", timeout)
        finally:
            original_error = sys.exc_info()[0] is not None
            cleanup_errors: list[str] = []
            try:
                docker([*command, "down", "--volumes", "--remove-orphans"], timeout=120)
            except (OSError, subprocess.SubprocessError):
                cleanup_errors.append("containers, networks or volumes")
            config = json.loads(resolved.read_text())
            for service in config["services"].values():
                if "build" in service:
                    try:
                        docker(["image", "rm", "-f", service["image"]], check=False)
                    except (OSError, subprocess.SubprocessError):
                        cleanup_errors.append("built image")
            if cleanup_errors:
                message = f"Cleanup incomplete for {identifier}: " + ", ".join(cleanup_errors)
                if not original_error:
                    raise ProjectError(message)
                print(f"WARNING: {message}", file=sys.stderr)

def run_project(project: Project, timeout: float = 60) -> None:
    missing = [name for name in project.required_env if not os.environ.get(name)]
    if missing:
        raise ProjectError("Set required environment variables before running: " + ", ".join(missing))
    if project.runtime_type == "compose":
        run_compose(project, timeout)
        return
    identifier = "portal-check-" + uuid.uuid4().hex
    cleanup_failed = False
    try:
        docker(["build", "-t", identifier, "-f", str(project.dockerfile), str(project.context)], timeout=600)
        env_args = [argument for name in project.required_env for argument in ("--env", name)]
        docker([
            "run", "--detach", "--name", identifier,
            "--publish", f"127.0.0.1::{project.port}", *env_args, identifier,
        ])
        address = docker(["port", identifier, f"{project.port}/tcp"])
        if not re.fullmatch(r"127\.0\.0\.1:[0-9]+", address):
            raise ProjectError("Docker did not return the expected local port binding.")
        wait_ready(f"http://{address}{project.health_path}", timeout)
    finally:
        original_error = sys.exc_info()[0] is not None
        for arguments in (["rm", "-f", identifier], ["image", "rm", "-f", identifier]):
            try:
                docker(arguments, check=False)
            except (OSError, subprocess.SubprocessError):
                cleanup_failed = True
        if cleanup_failed:
            message = f"Docker cleanup could not complete. Remove container/image {identifier} manually."
            if not original_error:
                raise ProjectError(message)
            print(f"WARNING: {message}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--run", action="store_true", help="Build and run this project's code locally using Docker.")
    parser.add_argument("--timeout", type=float, default=60, help="Readiness timeout in seconds (default: 60).")
    args = parser.parse_args()
    if not 0 < args.timeout <= 3600:
        parser.error("--timeout must be between 0 and 3600 seconds")
    try:
        project = check_project(args.directory)
        print("Project structure: PASS")
        if args.run:
            run_project(project, args.timeout)
            print("Docker build: PASS\nHTTP readiness: PASS")
        else:
            print("Docker build: NOT CHECKED\nHTTP readiness: NOT CHECKED\nUse --run to check locally with Docker.")
        print("Not checked: secret scanning, exercise correctness, learner isolation, cloud compatibility.")
        return 0
    except (ProjectError, OSError, subprocess.SubprocessError) as error:
        message = (
            str(error) if isinstance(error, ProjectError)
            else "Local Docker operation failed or timed out. "
            "Check Docker availability and your project locally."
        )
        print(f"FAIL: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
