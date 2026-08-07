import type { Conversation, AnalysisResult } from '../types.d';

/**
 * Serviço responsável por enviar a conversa ao backend FastAPI.
 * Em uma extensão MV3, o service worker não possui `process.env`; por isso
 * mantemos a URL fixa e simples para evitar erros de inicialização.
 */
const BACKEND_URL = 'http://127.0.0.1:8000/analyze';

export async function sendConversation(conversation: Conversation): Promise<AnalysisResult> {
  const payload = {
    chat_id: conversation.id ?? crypto.randomUUID(),
    canal: 'chrome-extension',
    mensagens: conversation.messages.map((m) => m.text).filter(Boolean)
  };

  // O worker/background fará a chamada fetch; centralizamos aqui para facilitar testes.
  const res = await fetch(BACKEND_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} - ${text}`);
  }

  const body = await res.json();

  // Mantem compatibilidade com o painel atual da extensao.
  return {
    reason: body.reason,
    sentiment: body.sentiment,
    quality: body.quality,
    trends: body.trends ?? {},
    insights: Array.isArray(body.insights_list)
      ? body.insights_list
      : body.insights
      ? [String(body.insights)]
      : []
  } as AnalysisResult;
}
