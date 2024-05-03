# SPDX-FileCopyrightText: 2024-present Benjamin Li <bli@riorey.com>
#
# SPDX-License-Identifier: MIT

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
    output = subprocess.run([
        '/bin/ipa-healthcheck',
        '--output-type', 'json',
        '--failures-only',
    ], capture_output=True, text=True, check=False)

    if output.returncode == 0:
        print('HEALTHCHECK OK')
        sys.exit(NagiosSeverity.OK)

    # Something is wrong
    result = json.loads(output.stdout)

    # Pull interesting data out - should be at least one failure here.
    failures: list[tuple[IpaSeverity, str]] = []
    for item in result:
        severity = IpaSeverity[item['result']]
        check = f"{item['source']}.{item['check']}.{item['kw']['key']}"
        msg = f"{check}: item['msg']"

        failures.append((severity, msg))

    # Sort by priority
    failures.sort(reverse=True)

    max_sev = failures[0][0]
    if max_sev >= IpaSeverity.ERROR:
        print('HEALTHCHECK CRITICAL:', failures[0][1])
        for other in failures[1:]:
            print(other[1])
        sys.exit(NagiosSeverity.CRITICAL)

    else:
        print('HEALTHCHECK WARNING:', failures[0][1])
        for other in failures[1:]:
            print(other[1])
        sys.exit(NagiosSeverity.WARNING)




if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('HEALTHCHECK UNKNOWN:', e)
        sys.exit(NagiosSeverity.UNKNOWN)
