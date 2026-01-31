class Config:
    """Set Flask configuration from .env file."""

    # Server
    HOST = '0.0.0.0'
    PORT = 5000
    DB_USERNAME = 'postgres'
    DB_PASSWORD = 'postgres'
    DB_NAME = 'mapmarket'
    DB_HOST = 'localhost'
    DB_PORT = 5432


    # Database
    SQLALCHEMY_DATABASE_URI = "postgresql://"+DB_USERNAME+":"+DB_PASSWORD+"@"+DB_HOST+"/"+DB_NAME
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # Swagger
    SWAGGER_PATH = "/swagger"
    SWAGGER_FILE = "/static/swagger.json"


    