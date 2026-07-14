from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]

OVMF_CODE_CANDIDATES = (
    "/usr/share/OVMF/OVMF_CODE.fd",
    "/usr/share/edk2-ovmf/x64/OVMF_CODE.fd",
    "/usr/share/edk2/x64/OVMF_CODE.fd",
)

OVMF_VARS_CANDIDATES = (
    "/usr/share/OVMF/OVMF_VARS.fd",
    "/usr/share/edk2-ovmf/x64/OVMF_VARS.fd",
    "/usr/share/edk2/x64/OVMF_VARS.fd",
)


@dataclass(frozen=True)
class AppRuntime:
    name: str
    generation: int
    generation_dir: str
    data_dir: str
    vm: Any

    def compose(self, *args: str, timeout: float = 120) -> Any:
        return self.vm.run(
            [
                "docker",
                "compose",
                "--project-name",
                self.name,
                "-f",
                f"{self.generation_dir}/docker-compose.yml",
                "--env-file",
                f"{self.generation_dir}/rugix-app.env",
                *args,
            ],
            hide=True,
            timeout=timeout,
        )

    def exec(self, service: str, *args: str, timeout: float = 120) -> Any:
        return self.compose("exec", "-T", service, *args, timeout=timeout)


@pytest.fixture(scope="session")
def testkit() -> Any:
    return pytest.importorskip("rugix_testkit")


@pytest.fixture(scope="session")
def vm(testkit: Any) -> Any:
    required_env = ["RUGIX_TEST_IMAGE", "RUGIX_TEST_SSH_KEY"]
    missing = [name for name in required_env if name not in os.environ]
    if missing:
        pytest.skip(f"VM test environment not configured: {', '.join(missing)}")

    image = Path(os.environ["RUGIX_TEST_IMAGE"]).resolve()
    private_key = Path(os.environ["RUGIX_TEST_SSH_KEY"]).resolve()
    ovmf_code = resolve_firmware("RUGIX_OVMF_CODE_AMD64", OVMF_CODE_CANDIDATES)
    ovmf_vars = resolve_firmware("RUGIX_OVMF_VARS_AMD64", OVMF_VARS_CANDIDATES)

    config = testkit.VMConfig(
        arch="x86_64",
        memory=3072,
        smp=2,
        drives=[testkit.Drive(file=image, overlay=True, size="16G")],
        pflash=[
            testkit.Pflash(file=ovmf_code, readonly=True),
            testkit.Pflash(file=ovmf_vars),
        ],
        extra_args=["-device", "virtio-rng-pci"],
    )

    with testkit.VMHandle.start(config, private_key=private_key, boot_timeout=420) as handle:
        handle.run(["docker", "compose", "version"], hide=True)
        yield handle


@pytest.fixture(scope="session")
def activate_app(vm: Any) -> Any:
    runtimes: dict[str, AppRuntime] = {}

    def _activate(app_name: str) -> AppRuntime:
        if app_name not in runtimes:
            bundle = bundle_path(app_name)
            remote_bundle = f"/tmp/{app_name}.rugixb"
            vm.upload(bundle, remote_bundle)
            run_checked(
                vm,
                [
                    "rugix-ctrl",
                    "apps",
                    "install",
                    "--insecure-skip-bundle-verification",
                    remote_bundle,
                ],
                timeout=900,
            )
            generation = 1
            run_checked(
                vm,
                ["rugix-ctrl", "apps", "activate", app_name, str(generation)],
                timeout=600,
            )
            info = wait_for_running(vm, app_name)
            assert info["name"] == app_name
            runtimes[app_name] = AppRuntime(
                name=app_name,
                generation=generation,
                generation_dir=f"/run/rugix/state/apps/{app_name}/generations/{generation}",
                data_dir=f"/run/rugix/state/apps/{app_name}/data",
                vm=vm,
            )
        return runtimes[app_name]

    return _activate


def bundle_path(app_name: str) -> Path:
    explicit = os.environ.get("RUGIX_APP_BUNDLE")
    explicit_app = os.environ.get("RUGIX_APP_NAME")
    if explicit and explicit_app == app_name:
        path = Path(explicit)
    else:
        bundle_dir = Path(os.environ.get("RUGIX_BUNDLE_DIR", ROOT / "dist"))
        path = bundle_dir / f"{app_name}.rugixb"
    if not path.is_file():
        pytest.skip(f"app bundle not built: {path}")
    return path.resolve()


def wait_for_running(vm: Any, app_name: str, timeout: float = 180) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        result = vm.run(["rugix-ctrl", "apps", "info", app_name], hide=True, check=False)
        last = result.stdout + result.stderr
        if result.return_code == 0:
            info = json.loads(result.stdout)
            if status_is_running(info.get("status")):
                return info
        time.sleep(3)
    raise AssertionError(f"app did not report running: {last}")


def run_checked(vm: Any, args: list[str], **kwargs: Any) -> Any:
    result = vm.run(args, hide=True, check=False, **kwargs)
    if result.return_code != 0:
        raise AssertionError(
            f"command failed ({result.return_code}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def status_is_running(status: object) -> bool:
    if status == "running":
        return True
    if isinstance(status, dict):
        return (
            "running" in status
            or status.get("type") == "running"
            or status.get("state") == "running"
        )
    return False


def resolve_firmware(env_var: str, candidates: tuple[str, ...]) -> Path:
    override = os.environ.get(env_var)
    if override:
        path = Path(override)
        if not path.exists():
            pytest.skip(f"{env_var}={override} does not exist")
        return path
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    pytest.skip(f"OVMF firmware not found; set {env_var} or install the ovmf package")
    raise AssertionError
