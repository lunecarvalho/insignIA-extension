# InsignIA

InsignIA é uma solução para análise inteligente de conversas de atendimento, combinando uma extensão para navegador com um backend baseado em FastAPI. O projeto foi construído para transformar interações de suporte em insights estruturados, facilitando a classificação de demandas, a avaliação de sentimento, a geração de resumos e a consolidação de resultados para análise operacional.

## Visão geral

A plataforma coleta mensagens de conversas em ambiente de navegação, processa o conteúdo com modelos de linguagem e gera informações úteis para equipes de atendimento e suporte. O fluxo inclui mascaramento de dados sensíveis, inferência de categoria e sentimento, cálculo de indicadores de qualidade e persistência dos resultados em uma planilha para acompanhamento e relatórios.

## Principais capacidades


- Análise automatizada de conversas de atendimento
- Classificação de intentos e categorias de demanda
- Inferência de sentimento inicial e final
- Geração de resumos e insights operacionais
- Avaliação de qualidade do atendimento com base em heurísticas
- Armazenamento estruturado dos resultados em Google Sheets
- Mecanismos de fallback para manter a experiência útil mesmo diante de falhas externas

## Arquitetura

- Frontend: extensão para Chrome com interface de interação e integração com o conteúdo da página
- Backend: serviço FastAPI responsável por receber, processar e consolidar os dados
- IA: integração com modelos hospedados no Hugging Face para classificação, sentimento e resumo
- Persistência: escrita de registros em planilha Google Sheets via conta de serviço
- Privacidade: mascaramento de dados pessoais antes da inferência por modelos externos

## Estrutura do projeto

- backend/app: API, configuração, modelos, serviços e repositórios
- src: lógica da extensão, incluindo background, content scripts e popup
- ui: interface da extensão
- backend/tests: testes automatizados para validação de comportamento e robustez

## Configuração local

1. Criar e ativar um ambiente virtual Python
2. Instalar as dependências do backend
3. Definir as variáveis de ambiente necessárias em backend/.env
4. Iniciar a API localmente
5. Compilar e carregar a extensão no Chrome para uso local

## Configuração de ambiente

As principais variáveis incluem credenciais e endpoints para Hugging Face, Google Sheets e parâmetros operacionais do backend. A configuração é feita por meio do arquivo backend/.env, com valores locais protegidos e não versionados.

## Refinamentos de fallback

O fluxo de fallback foi refinado para manter a análise útil mesmo quando os modelos externos não estão disponíveis. Entre os ajustes estão:

- priorização de palavras-chave para melhorar a classificação de categorias como impressora, login, financeiro, cancelamento, cardápio e sistema;
- heurísticas mais alinhadas ao atendimento real, incluindo reconhecimento de resolução, confirmação de resolução, empatia e cordialidade;
- geração de resumos mais coerentes com a categoria detectada, evitando descrições incompatíveis com o contexto da conversa.

## Testes

A suíte de testes do backend pode ser executada com:

```bash
pytest -q
```

Os testes cobrem cenários de mascaramento de dados, validação de payloads, heurísticas de qualidade e comportamento de fallback.
