# InsignIA API (MVP)

Backend FastAPI do MVP de analise inteligente usando Hugging Face + Google Sheets.

Veja o guia completo no README da raiz:

- setup local
- variaveis de ambiente
- Service Account do Google
- exemplos de request/response
- limitacoes conhecidas

Execucao rapida:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
