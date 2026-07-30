/**
 * Script para o popup da extensão.
 * - solicita extração ao content script ativo
 * - exibe estado simples e recebe resultados via mensagens
 */

const analyzeBtn = document.getElementById('popup-analyze-btn') as HTMLButtonElement | null;
const statusNode = document.getElementById('popup-status') as HTMLDivElement | null;
const summaryNode = document.getElementById('popup-summary') as HTMLDivElement | null;

function setStatus(text: string) {
  if (statusNode) statusNode.innerText = text;
}

async function triggerAnalysisFromPopup() {
  setStatus('Enviando solicitação ao conteúdo...');
  // envia mensagem para o tab ativo solicitando extração
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab || !tab.id) {
      setStatus('Nenhuma aba ativa encontrada');
      return;
    }

    chrome.tabs.sendMessage(tab.id, { type: 'startFromPopup' }, (response) => {
      if (chrome.runtime.lastError) {
        setStatus('Erro: conteúdo não responde nesta página');
        console.warn('InsignIA popup: sendMessage error', chrome.runtime.lastError.message);
        return;
      }

      setStatus('Análise em andamento — aguarde...');
    });
  });
}

if (analyzeBtn) {
  analyzeBtn.addEventListener('click', (e) => {
    analyzeBtn.disabled = true;
    triggerAnalysisFromPopup();
    setTimeout(() => (analyzeBtn.disabled = false), 2000);
  });
}

// Recebe resultado enviado pelo background e exibe resumo simples no popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'analysisResult') {
    const payload = message.payload;
    if (payload?.reason) {
      if (summaryNode) {
        summaryNode.innerHTML = `<strong>${payload.reason.category}</strong> — ${payload.reason.subcategory} <div style="color:#697386;font-size:12px">Confiança ${payload.reason.confidence}%</div>`;
      }
      setStatus('Análise concluída');
    } else if (payload?.error) {
      setStatus('Erro na análise: ' + payload.error);
    }
  }
  return true;
});

// Estado inicial do popup
setStatus('Pronto');
