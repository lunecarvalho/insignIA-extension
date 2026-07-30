"""
Inicializa o esquema do banco de dados (cria tabelas).
Execute com: `python -m app.db.init_db` a partir da pasta `backend`.
"""
from ..models import conversation, analysis  # ensure models are imported so metadata is registered
from .session import engine, Base


def init_db():
    print('Criando tabelas no banco de dados...')
    Base.metadata.create_all(bind=engine)
    print('Tabelas criadas com sucesso.')


if __name__ == '__main__':
    init_db()
