const setupEl = document.getElementById('setup');
const mainEl = document.getElementById('main');
const apiKeyInput = document.getElementById('apiKeyInput');
const saveKeyBtn = document.getElementById('saveKeyBtn');
const keyError = document.getElementById('keyError');
const logoutBtn = document.getElementById('logoutBtn');

const analyzeBtn = document.getElementById('analyzeBtn');
const freelancerToggle = document.getElementById('freelancerMode');
const loadingEl = document.getElementById('loading');
const errorEl = document.getElementById('error');
const resultsEl = document.getElementById('results');
const riskValue = document.getElementById('riskValue');
const summaryEl = document.getElementById('summary');
const clauseList = document.getElementById('clauseList');
const freelancerSection = document.getElementById('freelancerSection');
const freelancerList = document.getElementById('freelancerList');
const clearBtn = document.getElementById('clearBtn');

// ── Init ─────────────────────────────────────────────────────────────────────

chrome.storage.sync.get('apiKey', ({ apiKey }) => {
  if (apiKey) {
    showMain();
  } else {
    showSetup();
  }
});

function showSetup() {
  setupEl.classList.remove('hidden');
  mainEl.classList.add('hidden');
}

function showMain() {
  setupEl.classList.add('hidden');
  mainEl.classList.remove('hidden');
}

// ── API key setup ─────────────────────────────────────────────────────────────

saveKeyBtn.addEventListener('click', async () => {
  const key = apiKeyInput.value.trim();
  if (!key) return;

  saveKeyBtn.disabled = true;
  saveKeyBtn.textContent = 'Validating…';
  keyError.classList.add('hidden');

  try {
    const res = await fetch(`${await getApiBase()}/validate-key`, {
      headers: { 'X-API-Key': key },
    });

    if (!res.ok) {
      throw new Error('Invalid or inactive key. Check the key and try again.');
    }

    chrome.storage.sync.set({ apiKey: key }, () => {
      showMain();
    });
  } catch (err) {
    keyError.textContent = err.message;
    keyError.classList.remove('hidden');
  } finally {
    saveKeyBtn.disabled = false;
    saveKeyBtn.textContent = 'Save Key';
  }
});

logoutBtn.addEventListener('click', () => {
  chrome.storage.sync.remove('apiKey', () => {
    resultsEl.classList.add('hidden');
    errorEl.classList.add('hidden');
    apiKeyInput.value = '';
    showSetup();
  });
});

// ── Helpers ───────────────────────────────────────────────────────────────────

async function getApiBase() {
  return new Promise((resolve) => {
    chrome.storage.sync.get('apiKey', () => resolve('https://api.cautelioai.xyz'));
  });
}

function setLoading(on) {
  analyzeBtn.disabled = on;
  loadingEl.classList.toggle('hidden', !on);
}

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove('hidden');
}

function clearError() {
  errorEl.classList.add('hidden');
  errorEl.textContent = '';
}

function renderRisk(level) {
  riskValue.textContent = level.toUpperCase();
  riskValue.className = `risk-value ${level}`;
}

function renderClause(clause) {
  const card = document.createElement('div');
  card.className = `clause-card ${clause.risk_level || 'low'}`;
  const typeLabel = (clause.type || 'clause').replace(/_/g, ' ');

  card.innerHTML = `
    <div class="clause-header">
      <div class="clause-meta">
        <span class="clause-dot"></span>
        <span class="clause-type">${typeLabel}</span>
      </div>
      <span class="chevron">&#9660;</span>
    </div>
    <div class="clause-body">
      <div class="clause-explanation">${clause.explanation || ''}</div>
      ${clause.negotiation_tip ? `<div class="clause-tip">${clause.negotiation_tip}</div>` : ''}
    </div>
  `;

  card.querySelector('.clause-header').addEventListener('click', () => {
    card.classList.toggle('open');
  });

  return card;
}

// ── Analyze ───────────────────────────────────────────────────────────────────

analyzeBtn.addEventListener('click', () => {
  clearError();
  resultsEl.classList.add('hidden');
  setLoading(true);

  chrome.runtime.sendMessage(
    { type: 'ANALYZE', freelancer_mode: freelancerToggle.checked },
    (response) => {
      setLoading(false);

      if (chrome.runtime.lastError) {
        showError(chrome.runtime.lastError.message);
        return;
      }

      if (!response || response.error) {
        if (response?.error === 'no_key') {
          chrome.storage.sync.remove('apiKey', () => showSetup());
          return;
        }
        showError(response ? response.error : 'No response from background.');
        return;
      }

      const { analysis, isPdf } = response;

      renderRisk(analysis.overall_risk || 'low');
      summaryEl.textContent = analysis.summary || '';

      clauseList.innerHTML = '';
      const clauses = analysis.clauses || [];
      if (clauses.length === 0) {
        const none = document.createElement('p');
        none.style.cssText = 'font-size:12px;color:#555570;text-align:center;padding:8px 0';
        none.textContent = 'No high-risk clauses detected.';
        clauseList.appendChild(none);
      } else {
        clauses.forEach((c) => clauseList.appendChild(renderClause(c)));
      }

      freelancerList.innerHTML = '';
      const flags = analysis.freelancer_flags || [];
      if (freelancerToggle.checked && flags.length > 0) {
        flags.forEach((f) => {
          const li = document.createElement('li');
          li.textContent = f.issue || '';
          freelancerList.appendChild(li);
        });
        freelancerSection.classList.remove('hidden');
      } else {
        freelancerSection.classList.add('hidden');
      }

      clearBtn.style.display = isPdf ? 'none' : '';
      resultsEl.classList.remove('hidden');
    }
  );
});

clearBtn.addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    chrome.tabs.sendMessage(tab.id, { type: 'CLEAR_HIGHLIGHTS' });
  });
  resultsEl.classList.add('hidden');
  clearError();
});
