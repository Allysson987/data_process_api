# Data Process API

API desenvolvida em Python com FastAPI para coleta, armazenamento, consulta e gerenciamento de dados jurídicos, incluindo diários oficiais e informações processuais.

O projeto busca automatizar a obtenção de informações jurídicas, disponibilizando consultas por meio de endpoints REST e utilizando mecanismos de cache para otimizar o acesso aos dados.

## Funcionalidades

### 1. Coleta e sincronização de diários oficiais

- Captura automatizada de diários oficiais de **3 estados brasileiros**.
- Sincronização automática a cada 24 horas.
- Armazenamento dos registros coletados em banco de dados PostgreSQL (Neon).
- Utilização do Redis para cache das consultas.
- Consulta de diários por Unidade Federativa (UF).
- Ordenação dos resultados por data de publicação.
- Monitoramento do status das sincronizações.

### 2. Consulta de processos judiciais

- Integração com o DataJud, serviço de consulta pública do Conselho Nacional de Justiça (CNJ).
- Consulta de processos utilizando o número processual.
- Recuperação de informações processuais e andamentos disponíveis na fonte consultada.
- Disponibilização dos resultados por meio de API REST.

### 3. Autenticação e controle de acesso

- Autenticação baseada em JWT.
- Cadastro e gerenciamento de usuários.
- Senhas armazenadas utilizando hash seguro.
- Criptografia dos e-mails armazenados.
- Hash de e-mail para identificação e consultas.
- Controle de permissões administrativas.
- Limitação de requisições por usuário (Rate Limiting).

### 4. Cache e armazenamento

**PostgreSQL (Neon)**
- Persistência dos diários oficiais.
- Armazenamento dos dados processuais e demais registros da aplicação.

**Redis**
- Cache das consultas de diários oficiais.
- Armazenamento de informações de status das sincronizações.
- Redução de consultas repetidas ao banco de dados.

## Arquitetura

A aplicação utiliza uma arquitetura modular, separando responsabilidades entre endpoints, controladores, modelos, serviços e casos de uso.

```text
Data Process API
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── auth.py
│   │           └── process_search.py
│   │
│   ├── controllers/
│   │   └── controller_execution.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── security.py
│   │
│   ├── database/
│   │   └── connection.py
│   │
│   ├── models/
│   │
│   ├── use_cases/
│   │   ├── diary_cache_service.py
│   │   └── rate_limit.py
│   │
│   └── main.py
│
├── requirements.txt
├── Dockerfile
└── README.md
```

*Estrutura ilustrativa dos principais módulos, não necessariamente a listagem completa do projeto.*

## Endpoints

Base da API:

```text
/api
```

### Autenticação

Prefixo:

```text
/api/auth
```

Responsável pelas operações de autenticação e gerenciamento de acesso.

### Consulta e processamento

Prefixo:

```text
/api/process_search
```

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/diary/{uf}` | Consulta diários oficiais por estado |
| GET | `/diary/{uf}/status` | Consulta status da sincronização |
| GET | `/consult_case/{number_case}` | Consulta informações de um processo judicial |

### Documentação interativa

Com a aplicação em execução:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI: `/openapi.json`

## Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal |
| FastAPI | Desenvolvimento da API REST |
| SQLAlchemy | ORM e comunicação com banco de dados |
| PostgreSQL / Neon | Persistência de dados |
| Redis | Cache e controle de requisições |
| JWT | Autenticação |
| Argon2 | Hash de senhas |
| Cryptography | Criptografia de dados |
| DataJud / CNJ | Consulta de informações processuais |

## Execução do projeto

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd data_process_api
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
```

Ativação no Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto e configure as credenciais e parâmetros necessários para:

- Conexão PostgreSQL.
- Conexão Redis.
- Chave JWT.
- Segredo para hash de e-mail.
- Chave de criptografia de e-mail.

Não compartilhe o arquivo `.env` nem publique suas credenciais no repositório.

### 5. Executar a aplicação

```bash
uvicorn app.main:app --reload
```

A API ficará disponível localmente em:

```text
http://127.0.0.1:8000
```

Documentação:

```text
http://127.0.0.1:8000/docs
```

## Melhorias futuras

### 1. Expansão da coleta de dados jurídicos

- Implementar raspagem automatizada em diferentes tribunais.
- Ampliar a cobertura de fontes judiciais.
- Padronizar os dados coletados de diferentes sistemas e portais.

### 2. Extração de processos dos diários oficiais

- Desenvolver mecanismos de extração de números de processos a partir do conteúdo dos diários oficiais.
- Identificar referências processuais presentes nas publicações.
- Relacionar publicações aos respectivos processos judiciais.

### 3. Banco de dados de partes processuais

- Desenvolver uma estrutura para armazenamento de partes processuais.
- Identificar e relacionar partes aos números dos processos.
- Criar relacionamentos entre processos, partes e publicações oficiais.
- Permitir consultas por partes processuais e histórico de publicações.

### 4. Evolução da infraestrutura

- Aprimorar a distribuição das tarefas de coleta e processamento.
- Implementar processamento assíncrono e filas de mensagens.
- Melhorar o monitoramento das execuções.
- Expandir a estratégia de cache e otimizar consultas.

## Objetivo do projeto

Construir uma infraestrutura de coleta e processamento de informações jurídicas capaz de centralizar diários oficiais, processos judiciais, andamentos e futuramente dados de partes processuais.

A proposta é transformar informações jurídicas distribuídas em diferentes fontes em dados estruturados, persistentes e acessíveis por meio de uma API.