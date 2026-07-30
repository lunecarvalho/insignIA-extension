import type { Conversation, AnalysisResult } from './types.d';
import { normalizeConversation } from './utils/serializer';

// Content script: injeta botão, extrai conversa e renderiza painel lateral com resultados.

/**
 * Injeta um botão flutuante "Analisar Conversa" na página. O botão dispara extração.
 */
function injectAnalyzeButton() {
  if (document.getElementById('insignia-analyze-btn')) return;

  const btn = document.createElement('button');
  btn.id = 'insignia-analyze-btn';
  btn.innerText = '🔍 Analisar Conversa';
  Object.assign(btn.style, {
    position: 'fixed',
    right: '18px',
    bottom: '24px',
    zIndex: '999999',
    padding: '12px 14px',
    borderRadius: '12px',
    background: 'linear-gradient(135deg,#5b5ceb,#00d2c7)',
    color: 'white',
    border: 'none',
    boxShadow: '0 10px 30px rgba(16,24,40,0.12)',
    fontWeight: '700'
  });

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.innerText = '⏳ Extraindo...';
    try {
      const conv = extractConversation();
      // Envia a conversa para o background (service worker) para chamada à API.
      chrome.runtime.sendMessage({ type: 'analyze', conversation: conv }, (resp) => {
        // resposta é enviada assíncronamente via mensagem do background.
      });
    } catch (err) {
      console.error('InsignIA: erro ao extrair conversa', err);
    } finally {
      btn.disabled = false;
      btn.innerText = '🔍 Analisar Conversa';
    }
  });

  document.body.appendChild(btn);
}

/**
 * Heurística universal para tentar extrair mensagens de um chat/atendimento.
 * Não depende de um framework específico; tenta múltiplos seletores comuns.
 */
function extractConversation(): Conversation {
  // Tentativas de encontrar nós de mensagens em páginas de atendimento comuns.
  const selectors = [
    '[data-message]',
    '.message',
    '.chat-message',
    '.msg',
    '.bubble',
    'li.message',
    '.convo-item'
  ];

  let nodes: Element[] = [];
  for (const s of selectors) {
    const found = Array.from(document.querySelectorAll(s));
    if (found.length > 0) {
      nodes = found;
      break;
    }
  }

  // Fallback: procura por listas de parágrafos dentro de containers de chat
  if (nodes.length === 0) {
    const containers = Array.from(document.querySelectorAll('[role="log"], [aria-live]'));
    if (containers.length) {
      nodes = Array.from(containers[0].querySelectorAll('p,div,li'));
    }
  }

  // Transformar os nós localizados em objetos simples
  const raw = nodes.map((el) => {
    // procura por autor e texto dentro do nó
    const author = (el.querySelector('.author') || el.querySelector('.from') || el.getAttribute('data-author'))?.textContent?.trim();
    const text = (el.querySelector('.text') || el.querySelector('.content') || el).textContent?.trim() ?? '';
    const ts = el.getAttribute('data-time') || el.querySelector('time')?.getAttribute('datetime') || undefined;
    return { role: author ?? undefined, text, timestamp: ts };
  });

  return normalizeConversation(raw, window.location.href);
}

/**
 * Renderiza um painel lateral minimalista para apresentar os resultados.
 * O painel é injectado na página e recebe atualizações via mensagens.
 */
function ensurePanel(): HTMLElement {
  let panel = document.getElementById('insignia-panel');
  if (panel) return panel;

  panel = document.createElement('aside');
  panel.id = 'insignia-panel';
  panel.setAttribute('aria-hidden', 'false');
  Object.assign(panel.style, {
    position: 'fixed',
    right: '18px',
    top: '18px',
    width: '360px',
    height: '84vh',
    background: 'white',
    borderRadius: '16px',
    boxShadow: '0 24px 70px rgba(16,24,40,0.08)',
    border: '1px solid rgba(229,233,242,0.9)',
    zIndex: '999999',
    overflow: 'auto',
    padding: '14px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  });

  const header = document.createElement('div');
  header.style.display = 'flex';
  header.style.justifyContent = 'space-between';
  header.style.alignItems = 'center';

  const title = document.createElement('strong');
  title.innerText = 'InsignIA — Resultados';
  title.style.fontSize = '14px';

  const close = document.createElement('button');
  close.innerText = '✕';
  Object.assign(close.style, { background: 'transparent', border: 'none', cursor: 'pointer' });
  close.addEventListener('click', () => panel?.remove());

  header.appendChild(title);
  header.appendChild(close);
  panel.appendChild(header);

  const body = document.createElement('div');
  body.id = 'insignia-panel-body';
  body.style.display = 'flex';
  body.style.flexDirection = 'column';
  body.style.gap = '10px';
  panel.appendChild(body);

  document.body.appendChild(panel);
  return panel;
}

function renderAnalysis(result: AnalysisResult | { error?: string }) {
  const panel = ensurePanel();
  const body = panel.querySelector('#insignia-panel-body') as HTMLElement;
  body.innerHTML = '';

  if (!result || (result as any).error || !('reason' in result)) {
    const errorCard = document.createElement('div');
    errorCard.style.padding = '12px';
    errorCard.style.borderRadius = '12px';
    errorCard.style.border = '1px solid #ffe0e0';
    errorCard.innerHTML = `<h4 style="margin:0 0 6px 0">Falha na análise</h4>
    <div style="color:#b42318">Não foi possível conectar à API. Verifique se o backend FastAPI está rodando em http://127.0.0.1:8000.</div>`;
    body.appendChild(errorCard);
    return;
  }

  const resultData = result as AnalysisResult;

  const reasonCard = document.createElement('div');
  reasonCard.style.padding = '10px';
  reasonCard.style.borderRadius = '12px';
  reasonCard.style.border = '1px solid var(--border, #eef2ff)';
  reasonCard.innerHTML = `<h4 style="margin:0 0 6px 0">Motivo do Atendimento</h4>
  <div style="font-weight:700">${resultData.reason.category}</div>
  <div style="color:#697386;font-size:12px">${resultData.reason.subcategory}</div>
  <div style="margin-top:8px;font-weight:800">Confiança: ${resultData.reason.confidence}%</div>`;
  body.appendChild(reasonCard);

  const sentCard = document.createElement('div');
  sentCard.style.padding = '10px';
  sentCard.style.borderRadius = '12px';
  sentCard.style.border = '1px solid var(--border, #eef2ff)';
  sentCard.innerHTML = `<h4 style="margin:0 0 6px 0">Análise de Sentimento</h4>
  <div style="font-weight:700">${resultData.sentiment.label} (${resultData.sentiment.score})</div>`;
  body.appendChild(sentCard);

  const qCard = document.createElement('div');
  qCard.style.padding = '10px';
  qCard.style.borderRadius = '12px';
  qCard.style.border = '1px solid var(--border, #eef2ff)';
  const checklistHtml = Object.entries(resultData.quality.checklist)
    .map(([k, v]) => `<div>${v ? '✔' : '✖'} ${k}</div>`)
    .join('');
  qCard.innerHTML = `<h4 style="margin:0 0 6px 0">Qualidade do Atendimento</h4>
  <div style="font-weight:800">${resultData.quality.score}/100</div>
  <div style="margin-top:8px">${checklistHtml}</div>
  <div style="margin-top:8px;color:#697386">${resultData.quality.notes ?? ''}</div>`;
  body.appendChild(qCard);

  const iCard = document.createElement('div');
  iCard.style.padding = '10px';
  iCard.style.borderRadius = '12px';
  iCard.style.border = '1px solid var(--border, #eef2ff)';
  iCard.innerHTML = `<h4 style="margin:0 0 6px 0">Insights da IA</h4>
  <ul style="margin:0;padding-left:18px">${resultData.insights.map((i) => `<li>${i}</li>`).join('')}</ul>`;
  body.appendChild(iCard);
}

// Recebe mensagens do background/service worker.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'analysisResult') {
    try {
      renderAnalysis(message.payload as AnalysisResult | { error?: string });
    } catch (err) {
      console.error('InsignIA: erro ao renderizar análise', err);
    }
  }
  return true;
});

// Permite que o popup dispare a extração via mensagem
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'startFromPopup') {
    try {
      const conv = extractConversation();
      chrome.runtime.sendMessage({ type: 'analyze', conversation: conv });
      sendResponse({ status: 'ok' });
    } catch (err) {
      sendResponse({ status: 'error', message: String(err) });
    }
  }
  return true;
});

// Inicialização: injeta botão quando o documento estiver pronto.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectAnalyzeButton);
} else {
  injectAnalyzeButton();
}
