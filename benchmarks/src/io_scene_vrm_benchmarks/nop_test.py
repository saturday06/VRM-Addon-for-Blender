# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import pytest
from pytest_codspeed.plugin import BenchmarkFixture


def test_nop(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def _() -> None:
        for _ in range(10):
            pass


if __name__ == "__main__":
    pytest.main()
