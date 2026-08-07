# InsignIA MVP (Chrome Extension + FastAPI)

MVP para analisar conversas de atendimento usando modelos do Hugging Face e salvar os resultados no Google Sheets.

## Fluxo geral

1. A extensao coleta mensagens da conversa no navegador.
2. O backend FastAPI recebe o payload em `POST /analyze`.
3. O texto e mascarado (PII) antes das chamadas de IA.
4. O backend chama os modelos:
	 - Sentimento: `cardiffnlp/twitter-xlm-roberta-base-sentiment`
	 - Zero-shot de motivo: `facebook/bart-large-mnli`
	 - Resumo: `csebuetnlp/mT5_multilingual_XLSum`
5. Calcula `qualidade_score` por heuristica simples.
6. Persiste resultado na aba `atendimentos` do Google Sheets.
7. Retorna JSON consolidado para a extensao.

## Estrutura relevante do backend

- `backend/app/main.py`: API, endpoint `/analyze`, CORS e tratamento padrao de erro.
- `backend/app/models.py`: contratos Pydantic de request/response.
- `backend/app/services/pii_mask.py`: mascaramento de email/telefone/CPF.
- `backend/app/services/hf_client.py`: cliente HTTP da Inference API com timeout, retry e logs de latencia.
- `backend/app/services/sheets_client.py`: escrita no Google Sheets via Service Account.
- `backend/app/services/analyzer.py`: orquestracao da analise, fallbacks e persistencia.

## Setup local (5-10 min)

### 1) Backend

No terminal, na pasta `backend`:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copie `backend/.env.example` para `backend/.env` e preencha os valores.

Suba a API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Extensao

No terminal da raiz do projeto:

```bash
npm install
npm run build
```

Depois carregue a pasta da extensao em `chrome://extensions` (modo desenvolvedor).

## Configuracao `.env`

Variaveis obrigatorias para o MVP:

- `HF_API_TOKEN`
- `HF_SENTIMENT_MODEL` (default no exemplo)
- `HF_ZERO_SHOT_MODEL` (default no exemplo)
- `HF_SUMMARY_MODEL` (default no exemplo)
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON` (JSON completo em linha unica)

Variaveis uteis:

- `CORS_ORIGINS` (origens separadas por virgula, incluindo `chrome-extension://<id>`)
- `MAX_TEXT_CHARS` (default 12000)
- `HF_TIMEOUT_SECONDS`
- `HF_MAX_RETRIES`
- `GOOGLE_SHEETS_TAB_NAME` (default `atendimentos`)

## Google Sheets + Service Account

1. Crie um projeto no Google Cloud.
2. Habilite a API Google Sheets.
3. Crie uma Service Account.
4. Gere a chave JSON da Service Account.
5. Copie o conteudo JSON para `GOOGLE_SERVICE_ACCOUNT_JSON` (em uma linha).
6. Compartilhe a planilha com o e-mail da Service Account como Editor.

### Aba esperada

Nome da aba: `atendimentos`.

Colunas esperadas:

`timestamp, chat_id, canal, texto_conversa, categoria, categoria_score, sentimento_inicial, sentimento_final, qualidade_score, resumo, insights, status_erro`

Se a aba nao existir, crie manualmente no Google Sheets com este nome.

## Exemplo de request

`POST /analyze`

```json
{
	"chat_id": "chat-2026-0001",
	"canal": "whatsapp",
	"mensagens": [
		"Ola, estou com problema no login.",
		"Sinto muito pelo transtorno, vou te orientar no reset de senha.",
		"Perfeito, consegui entrar. Obrigado!"
	]
}
```

## Exemplo de response

```json
{
	"timestamp": "2026-08-02T12:00:00.000000+00:00",
	"chat_id": "chat-2026-0001",
	"canal": "whatsapp",
	"texto_conversa": "Ola, estou com problema no login...",
	"categoria": "Login",
	"categoria_score": 0.92,
	"sentimento_inicial": { "label": "Negativo", "score": 0.81 },
	"sentimento_final": { "label": "Positivo", "score": 0.88 },
	"qualidade_score": 100,
	"resumo": "Cliente iniciou com dificuldade de login e recebeu orientacao de reset...",
	"insights": "Atendimento consistente para Login; manter roteiro atual e replicar boas praticas.",
	"status_erro": "",
	"reason": { "category": "Login", "subcategory": "Geral", "confidence": 92 },
	"sentiment": { "label": "positive", "score": 0.88 },
	"quality": {
		"score": 100,
		"checklist": {
			"saudacao": true,
			"empatia_quando_reclamacao": true,
			"orientacao_solucao": true,
			"confirmacao_encerramento": true,
			"sentimento_final_positivo_ou_melhora": true
		}
	},
	"trends": {},
	"insights_list": [
		"Atendimento consistente para Login; manter roteiro atual e replicar boas praticas."
	]
}
```

## Limites e fallbacks do MVP

- Texto truncado para `MAX_TEXT_CHARS` antes de inferencia.
- Se resumo falhar: usa template local.
- Se classificacao falhar: categoria `Outro`.
- Se sentimento falhar: `Neutro`.
- Se gravacao no Sheets falhar: API retorna erro amigavel e log tecnico no backend.

## Testes minimos

Na pasta `backend`:

```bash
pytest -q
```

Cobertura minima incluida:

- mascaramento de PII
- validacao de payload `/analyze`
- heuristica de `qualidade_score`
- parser dos 3 modelos (com mock)
- fallback quando Hugging Face falha
