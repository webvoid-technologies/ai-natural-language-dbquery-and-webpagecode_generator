const questionInput = document.querySelector('#question-input');
const queryForm = document.querySelector('#query-form');
const queryButton = document.querySelector('#query-button');
const resultCard = document.querySelector('#result-card');
const resultContent = document.querySelector('#result-content');
const sqlBox = document.querySelector('#sql-box');
const sqlCode = document.querySelector('#sql-code');
const resultMeta = document.querySelector('#result-meta');
const validationBadge = document.querySelector('#validation-badge');
const retryMeta = document.querySelector('#retry-meta');
const timeMeta = document.querySelector('#time-meta');
const rowsMeta = document.querySelector('#rows-meta');
const resultActions = document.querySelector('#result-actions');
const aiLoading = document.querySelector('#ai-loading');
const sqlEditorWrap = document.querySelector('#sql-editor-wrap');
const sqlEditor = document.querySelector('#sql-editor');

const notify = window.notify || ((msg) => alert(msg));
let currentCsv = '';
let lastQuestion = '';

function setLoading(isLoading) {
  queryButton.disabled = isLoading;
  queryButton.querySelector('.btn-text').hidden = isLoading;
  queryButton.querySelector('.btn-spinner').hidden = !isLoading;
  aiLoading.hidden = !isLoading;
}

function renderError(message) {
  resultContent.innerHTML = `<div class="error-panel"><span>!</span><div><strong>Could not complete query</strong><p>${message}</p></div></div>`;
}

function renderResult(payload, question) {
  lastQuestion = question || lastQuestion;
  sqlCode.textContent = payload.sql;
  sqlBox.hidden = false;
  resultMeta.hidden = false;
  resultActions.hidden = false;
  sqlEditorWrap.hidden = true;

  validationBadge.textContent = payload.valid ? 'Valid SQL' : 'Invalid SQL';
  validationBadge.className = `badge ${payload.valid ? 'success' : 'error'}`;
  retryMeta.textContent = `Retries: ${payload.retry_count}`;
  timeMeta.textContent = `${payload.execution_time}s`;
  rowsMeta.textContent = `${payload.row_count} rows`;

  if (payload.row_count) {
    resultContent.innerHTML = payload.html_table || '<p>No results.</p>';
  } else {
    resultContent.innerHTML = `<div class="empty-results"><strong>No rows returned</strong><p>The query ran successfully but nothing matched. Try broadening your question.</p></div>`;
  }
  currentCsv = payload.csv || '';
}

function beginRequest() {
  resultCard.hidden = false;
  resultContent.replaceChildren();
  sqlBox.hidden = true;
  resultMeta.hidden = true;
  resultActions.hidden = true;
  sqlEditorWrap.hidden = true;
  setLoading(true);
  resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function executeQuery(question) {
  if (!question) return;
  beginRequest();

  try {
    const response = await fetch('/database/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Query failed.');

    renderResult(payload, question);
    notify('Query executed successfully.');
  } catch (error) {
    renderError(error.message);
    notify(error.message, true);
  } finally {
    setLoading(false);
  }
}

async function executeEditedSql(sql) {
  if (!sql) return;
  beginRequest();

  try {
    const response = await fetch('/database/execute-direct', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: lastQuestion || 'Edited SQL query', sql }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Query failed.');

    renderResult(payload, lastQuestion);
    notify('Edited SQL executed.');
  } catch (error) {
    renderError(error.message);
    notify(error.message, true);
  } finally {
    setLoading(false);
  }
}

queryForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  executeQuery(questionInput.value.trim());
});

questionInput?.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault();
    executeQuery(questionInput.value.trim());
  }
});

document.querySelectorAll('#example-chips .chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    questionInput.value = chip.dataset.query;
    executeQuery(chip.dataset.query);
  });
});

document.querySelector('#edit-sql')?.addEventListener('click', () => {
  sqlEditor.value = sqlCode.textContent;
  sqlEditorWrap.hidden = false;
  sqlEditor.focus();
});

document.querySelector('#cancel-edit')?.addEventListener('click', () => {
  sqlEditorWrap.hidden = true;
});

document.querySelector('#run-edited-sql')?.addEventListener('click', () => {
  executeEditedSql(sqlEditor.value.trim());
});

document.querySelector('#copy-sql')?.addEventListener('click', async () => {
  if (!sqlCode.textContent) return;
  await navigator.clipboard.writeText(sqlCode.textContent);
  notify('SQL copied to clipboard.');
});

document.querySelector('#download-csv')?.addEventListener('click', () => {
  if (!currentCsv) return notify('No CSV data available.', true);
  const blob = new Blob([currentCsv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'query-results.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  notify('CSV downloaded.');
});

// Deep-link: /database?q=... auto-fills and runs (used by "Run again" in history).
const presetQuestion = new URLSearchParams(location.search).get('q');
if (presetQuestion && questionInput) {
  questionInput.value = presetQuestion;
  executeQuery(presetQuestion);
}
