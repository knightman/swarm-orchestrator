from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    docker_host: str = "unix:///var/run/docker.sock"
    registry_url: str = "http://localhost:5000"
    database_path: str = "./data/swarm_orchestrator.db"
    definitions_dir: str = "./definitions"
    projects_dir: str = "/projects"
    health_check_interval: int = 30
    host: str = "0.0.0.0"
    port: int = 8080

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def db_path(self) -> Path:
        p = Path(self.database_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def defs_path(self) -> Path:
        return Path(self.definitions_dir)

    @property
    def projects_path(self) -> Path:
        return Path(self.projects_dir)


settings = Settings()
