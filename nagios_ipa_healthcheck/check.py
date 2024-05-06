# SPDX-FileCopyrightText: 2024-present Benjamin Li <bli@linsang.com>
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
    # Pull interesting data out - should be at least one failure here.
    failures = parse_checks(output.stdout)

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


def parse_checks(data: str) -> list[tuple[IpaSeverity, str]]:
    """Parse the output of ipa-healthcheck.

    Returns a list of failures, sorted by priority descending.

    Each failure is reported as (severity, human-readable description)"""
    result = json.loads(data)

    failures: list[tuple[IpaSeverity, str]] = []
    for item in result:
        severity = IpaSeverity[item["result"]]

        check = f"{item['source']}.{item['check']}"
        if "key" in item["kw"]:
            check += f".{item['kw']['key']}"

        if "msg" in item["kw"]:
            msg = f"{check}: {item['kw']['msg']}"
        else:
            msg = check

        failures.append((severity, msg))

    # Sort by priority
    failures.sort(reverse=True)

    return failures


if __name__ == "__main__":
    main()
