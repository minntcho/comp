import os

import pytest


pytestmark = pytest.mark.mysql


def _database_config() -> dict[str, object]:
    host = os.environ.get("COMP_TEST_MYSQL_HOST")
    if not host:
        pytest.skip("COMP_TEST_MYSQL_HOST is required for MySQL spine tests")
    return {
        "host": host,
        "port": int(os.environ.get("COMP_TEST_MYSQL_PORT", "3306")),
        "user": os.environ.get("COMP_TEST_MYSQL_USER", "comp"),
        "password": os.environ.get("COMP_TEST_MYSQL_PASSWORD", "comp"),
        "database": os.environ.get("COMP_TEST_MYSQL_DATABASE", "comp_test"),
        "charset": "utf8mb4",
        "autocommit": False,
    }


def test_mysql_spine_module_exists():
    from comp.persistence.mysql import apply_trust_spine_schema

    assert apply_trust_spine_schema is not None
