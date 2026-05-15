const API_BASE = 'https://api.cautelioai.xyz';

function isPdf(url) {
  try {
    return new URL(url).pathname.toLowerCase().endsWith('.pdf');
  } catch {
    return false;
  }
}

async function getApiKey() {
  return new Promise((resolve) => {
    chrome.storage.sync.get('apiKey', (r) => resolve(r.apiKey || null));
  });
}

async function analyzeHtmlPage(tab, apiKey, freelancerMode) {
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js'],
  }).catch(() => {});

  const [{ result: text }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.innerText.slice(0, 50000),
  });

  if (!text || text.trim().length < 100) {
    return { error: 'Not enough text found on this page. Make sure the contract is visible.' };
  }

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    body: JSON.stringify({ text, freelancer_mode: freelancerMode }),
  });

  if (!res.ok) {
    return { error: `Backend error (${res.status}): ${await res.text()}` };
  }

  const analysis = await res.json();

  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js'],
  }).catch(() => {});

  chrome.tabs.sendMessage(tab.id, {
    type: 'HIGHLIGHT_CLAUSES',
    clauses: analysis.clauses || [],
  });

  return { ok: true, analysis };
}

async function analyzePdf(tab, apiKey, freelancerMode) {
  const pdfRes = await fetch(tab.url, { credentials: 'include' });
  if (!pdfRes.ok) {
    return { error: `Could not fetch PDF (${pdfRes.status}). The file may require login.` };
  }

  const blob = await pdfRes.blob();
  const form = new FormData();
  form.append('file', blob, 'contract.pdf');
  form.append('freelancer_mode', freelancerMode ? 'true' : 'false');

  const res = await fetch(`${API_BASE}/analyze-pdf`, {
    method: 'POST',
    headers: { 'X-API-Key': apiKey },
    body: form,
  });

  if (!res.ok) {
    return { error: `Backend error (${res.status}): ${await res.text()}` };
  }

  const analysis = await res.json();
  return { ok: true, analysis, isPdf: true };
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type !== 'ANALYZE') return;

  (async () => {
    try {
      const apiKey = await getApiKey();
      if (!apiKey) {
        sendResponse({ error: 'no_key' });
        return;
      }

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const result = isPdf(tab.url)
        ? await analyzePdf(tab, apiKey, msg.freelancer_mode || false)
        : await analyzeHtmlPage(tab, apiKey, msg.freelancer_mode || false);

      sendResponse(result);
    } catch (err) {
      const message = err.message.includes('fetch')
        ? 'Cannot reach backend. Is it running?'
        : err.message;
      sendResponse({ error: message });
    }
  })();

  return true;
});
