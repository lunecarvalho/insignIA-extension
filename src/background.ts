import { sendConversation } from './services/api';
import type { Conversation } from './types.d';

/**
 * Background service worker (Manifest V3 service_worker)
 * - recebe mensagens do content script ou popup
 * - realiza chamadas ao backend FastAPI
 * - encaminha o resultado para o tab de origem
 */

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'analyze') {
    handleAnalyze(message.conversation as Conversation, sender);
    return true;
  }
});

async function handleAnalyze(conversation: Conversation, sender: chrome.runtime.MessageSender | undefined) {
  try {
    // Chamada ao backend
    const result = await sendConversation(conversation);

    // envia resultado ao tab que originou a solicitação
    const tabId = sender?.tab?.id;
    if (typeof tabId === 'number') {
      chrome.tabs.sendMessage(tabId, { type: 'analysisResult', payload: result });
    }
  } catch (err) {
    console.error('InsignIA background: erro ao analisar conversa', err);
    const tabId = sender?.tab?.id;
    if (typeof tabId === 'number') {
      chrome.tabs.sendMessage(tabId, { type: 'analysisResult', payload: { error: String(err) } });
    }
  }
}
