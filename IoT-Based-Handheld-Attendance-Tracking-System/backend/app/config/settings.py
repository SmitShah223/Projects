"""
config/settings.py — Application configuration via environment variables.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    # AWS IoT Core
    aws_iot_endpoint: str
    aws_region: str = "ap-south-1"
    iot_cert_path: str = "certs/server.crt.pem"
    iot_key_path: str  = "certs/server.key.pem"
    iot_ca_path: str   = "certs/AmazonRootCA1.pem"

    # App security
    secret_key: str
    admin_username: str = "admin"
    admin_password: str

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"

settings = Settings()
