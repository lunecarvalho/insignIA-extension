import type { Conversation, Message } from '../types.d';

/**
 * Normaliza e valida a estrutura da conversa antes de enviar para o backend.
 * Mantém um schema simples: { id?, url?, messages: [{role, text, timestamp}] }
 */
export function normalizeConversation(raw: any, sourceUrl?: string): Conversation {
  const conv: Conversation = {
    id: raw?.id ?? `conv_${Date.now()}`,
    url: sourceUrl ?? raw?.url ?? window.location.href,
    messages: []
  };

  const items = Array.isArray(raw) ? raw : raw?.messages ?? [];

  for (const m of items) {
    const msg: Message = {
      role: m?.role ?? m?.author ?? (m?.from ? String(m.from) : 'unknown'),
      text: String(m?.text ?? m?.content ?? m?.message ?? '').trim(),
      timestamp: m?.timestamp ?? m?.time ?? undefined
    };

    if (msg.text) conv.messages.push(msg);
  }

  return conv;
}
