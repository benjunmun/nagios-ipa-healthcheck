# SPDX-FileCopyrightText: 2024-present Benjamin Li <bli@linsang.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path

from nagios_ipa_healthcheck import check


def test_parse() -> None:
    data = Path(__file__).with_name("example.json").read_text()

    checks = check.parse_checks(data)

    assert len(checks) == 3

    assert checks[-1][0] == check.IpaSeverity.WARNING
