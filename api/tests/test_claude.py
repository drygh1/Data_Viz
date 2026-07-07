import pytest

from fishfinder.claude import SqlValidationError, validate_sql


def test_accepts_plain_select() -> None:
    validate_sql("SELECT signal FROM visits WHERE array = 'BigEddy'")


def test_accepts_with_cte() -> None:
    validate_sql(
        "WITH recent AS (SELECT * FROM visits WHERE arrived_at > '2026-06-20') "
        "SELECT signal FROM recent"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM visits",
        "DROP TABLE visits",
        "INSERT INTO visits VALUES (1)",
        "ATTACH 'other.db'",
        "PRAGMA database_list",
        "SELECT * FROM visits; DROP TABLE visits;",
        "not sql at all",
    ],
)
def test_rejects_unsafe_or_invalid_sql(sql: str) -> None:
    with pytest.raises(SqlValidationError):
        validate_sql(sql)
