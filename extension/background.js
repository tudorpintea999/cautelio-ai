// Switch to http://localhost:8000 for local development
const API_BASE = 'https://api.cautelioai.xyz';

function isPdf(url) {
  try {
    const path = new URL(url).pathname.toLowerCase();
    return path.endsWith('.pdf');
  } catch {
    return false;
  }
}

async function analyzeHtmlPage(tab, freelancerMode) {
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, freelancer_mode: freelancerMode }),
  });

  if (!res.ok) {
    return { error: `Backend error (${res.status}): ${await res.text()}` };
  }

  const analysis = await res.json();

  // Highlight clauses in-page
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

async function analyzePdf(tab, freelancerMode) {
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
    body: form,
  });

  if (!res.ok) {
    return { error: `Backend error (${res.status}): ${await res.text()}` };
  }

  const analysis = await res.json();
  // No in-page highlighting for native PDF viewer
  return { ok: true, analysis, isPdf: true };
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type !== 'ANALYZE') return;

  (async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const result = isPdf(tab.url)
        ? await analyzePdf(tab, msg.freelancer_mode || false)
        : await analyzeHtmlPage(tab, msg.freelancer_mode || false);
      sendResponse(result);
    } catch (err) {
      const message = err.message.includes('fetch')
        ? 'Cannot reach backend. Is it running on port 8000?'
        : err.message;
      sendResponse({ error: message });
    }
  })();

  return true;
});
