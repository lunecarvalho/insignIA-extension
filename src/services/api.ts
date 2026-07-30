import type { Conversation, AnalysisResult } from '../types.d';

/**
 * Serviço responsável por enviar a conversa ao backend FastAPI.
 * Em uma extensão MV3, o service worker não possui `process.env`; por isso
 * mantemos a URL fixa e simples para evitar erros de inicialização.
 */
const BACKEND_URL = 'http://127.0.0.1:8000/api/analisar';

export async function sendConversation(conversation: Conversation): Promise<AnalysisResult> {
  // O worker/background fará a chamada fetch; centralizamos aqui para facilitar testes.
  const res = await fetch(BACKEND_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(conversation)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} - ${text}`);
  }

  const body = await res.json();
  return body as AnalysisResult;
}
