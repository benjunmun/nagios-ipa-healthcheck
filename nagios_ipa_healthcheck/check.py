# SPDX-FileCopyrightText: 2024-present Benjamin Li <bli@riorey.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
import json
import subprocess
import sys


@enum.unique
class NagiosSeverity(enum.IntEnum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


@enum.unique
class IpaSeverity(enum.IntEnum):
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


def main() -> None:
    try:
        run_check()
    except Exception as e:  # noqa: BLE001
        sys.stdout.write("HEALTHCHECK UNKNOWN:")
        sys.stdout.write(str(e))
        sys.stdout.write("\n")
        sys.exit(NagiosSeverity.UNKNOWN)


def run_check() -> None:
    output = subprocess.run(
        [
            "/bin/ipa-healthcheck",
            "--output-type",
            "json",
            "--failures-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if output.returncode == 0:
        sys.stdout.write("HEALTHCHECK OK\n")
        sys.exit(NagiosSeverity.OK)

    # Something is wrong
    result = json.loads(output.stdout)

    # Pull interesting data out - should be at least one failure here.
    failures: list[tuple[IpaSeverity, str]] = []
    for item in result:
        severity = IpaSeverity[item["result"]]
        check = f"{item['source']}.{item['check']}.{item['kw']['key']}"
        msg = f"{check}: {item['kw']['msg']}"

        failures.append((severity, msg))

    # Sort by priority
    failures.sort(reverse=True)

    max_sev = failures[0][0]
    if max_sev >= IpaSeverity.ERROR:
        nagios_result = IpaSeverity.ERROR
    else:
        nagios_result = IpaSeverity.WARNING

    sys.stdout.write("HEALTHCHECK ")
    sys.stdout.write(nagios_result.name)
    sys.stdout.write(": ")
    sys.stdout.write(failures[0][1])
    sys.stdout.write("\n")
    for other in failures[1:]:
        sys.stdout.write(other[1])
        sys.stdout.write("\n")

    sys.exit(int(nagios_result))
