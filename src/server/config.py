"""Environment-driven settings for the gRPC server and DB pool."""

from __future__ import annotations

import dataclasses
import os

from dotenv import load_dotenv

load_dotenv()


@dataclasses.dataclass(frozen=True)
class Settings:
    database_url: str
    grpc_host: str
    grpc_port: int
    db_pool_min_size: int
    db_pool_max_size: int
    db_command_timeout_seconds: float
    default_loan_period_days: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ.get(
                "DATABASE_URL",
                "postgresql://USERNAME:PASSWORD@localhost:5432/DBNAME",
            ),
            grpc_host=os.environ.get("GRPC_HOST", "[::]"),
            grpc_port=int(os.environ.get("GRPC_PORT", "50051")),
            db_pool_min_size=int(os.environ.get("DB_POOL_MIN_SIZE", "5")),
            db_pool_max_size=int(os.environ.get("DB_POOL_MAX_SIZE", "20")),
            db_command_timeout_seconds=float(
                os.environ.get("DB_COMMAND_TIMEOUT_SECONDS", "20")
            ),
            default_loan_period_days=int(
                os.environ.get("DEFAULT_LOAN_PERIOD_DAYS", "14")
            ),
        )


settings = Settings.from_env()
