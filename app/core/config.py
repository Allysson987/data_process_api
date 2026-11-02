from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Classe responsável por carregar e validar as variáveis de ambiente.
    O Pydantic lê automaticamente o arquivo .env da raiz do projeto.
    """
    # Exemplo de variáveis de ambiente obrigatórias e opcionais
    APP_NAME: str = "Data Process API"
    ENVIRONMENT: str = "development"  # Se não estiver no .env, a API falha ao iniciar!
    DATA_JUD_SECRET_KEY: str
    
    # Configuração para ler o arquivo .env na raiz
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignora variáveis extras que estejam no .env mas não declaradas aqui
    )

# Instância global de configurações para ser importada no resto do projeto
settings = Settings()