from functools import cache
from pathlib import Path
from typing import Optional, Self


class SQLoader:
    _instance = None
    _initialized = False
    _sql_path = Path(__file__).parent / "sql"

    def __init__(self) -> None:
        if self._initialized:
            return

        self.sql_files: dict[str, Path] = {}
        self._scan_sql_dir()
        self._initialized = True

    def __new__(cls) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def _scan_sql_dir(self) -> None:
        files = self._sql_path.glob("**/*.sql")
        self.sql_files = {file.stem: file for file in files}

    @cache
    def load(self, sql_name: str, scan: bool = False) -> Optional[str]:
        if scan:
            self._scan_sql_dir()

        file = self.sql_files.get(sql_name)

        if not file:
            print(f"sql file with name {sql_name}.sql does not exist")
            return None

        with open(file, "r", encoding="utf-8") as f:
            sql = f.read()

        return sql
