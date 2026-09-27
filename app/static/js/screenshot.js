const fileInput = document.querySelector('#file-input');
const dropZone = document.querySelector('#drop-zone');
const uploadStatus = document.querySelector('#upload-status');
const imagePreviewWrap = document.querySelector('#image-preview-wrap');
const imagePreview = document.querySelector('#image-preview');
const generateButton = document.querySelector('#generate-button');
const resultCard = document.querySelector('#result-card');
const aiLoading = document.querySelector('#ai-loading');
const toast = document.querySelector('#toast');
const tabs = document.querySelectorAll('.tab');
const tabPanels = document.querySelectorAll('.tab-panel');
const htmlEditor = document.querySelector('#html-editor');
const cssEditor = document.querySelector('#css-editor');
const previewIframe = document.querySelector('#preview-iframe');
const segButtons = document.querySelectorAll('.seg-btn');
const removeImageBtn = document.querySelector('#remove-image');

let uploadedImageUrl = '';
let currentHtml = '';
let currentCss = '';

const notify = window.notify || ((msg) => alert(msg));

function setUploading(isUploading, message = '') {
  dropZone.classList.toggle('processing', isUploading);
  uploadStatus.hidden = !isUploading;
  uploadStatus.textContent = message;
}

function setGenerating(isGenerating) {
  generateButton.disabled = isGenerating;
  generateButton.querySelector('.btn-text').hidden = isGenerating;
  generateButton.querySelector('.btn-spinner').hidden = !isGenerating;
  aiLoading.hidden = !isGenerating;
}

function switchTab(name) {
  tabs.forEach((tab) => {
    const active = tab.dataset.tab === name;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', String(active));
  });
  tabPanels.forEach((panel) => {
    panel.hidden = !panel.id.endsWith(name);
    panel.classList.toggle('active', !panel.hidden);
  });
}

tabs.forEach((tab) => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));

async function upload(file) {
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  setUploading(true, `Uploading ${file.name}…`);
  try {
    const response = await fetch('/webpage/upload', { method: 'POST', body: form });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Upload failed.');
    uploadedImageUrl = payload.image_url;
    imagePreview.src = uploadedImageUrl;
    imagePreviewWrap.hidden = false;
    generateButton.disabled = false;
    notify('Screenshot uploaded. Click Generate to create code.');
  } catch (error) {
    notify(error.message, true);
  } finally {
    setUploading(false);
    fileInput.value = '';
  }
}

fileInput?.addEventListener('change', (event) => upload(event.target.files[0]));

// Keyboard access: Enter/Space on the drop zone opens the file picker.
dropZone?.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    fileInput.click();
  }
});

removeImageBtn?.addEventListener('click', () => {
  uploadedImageUrl = '';
  imagePreview.src = '';
  imagePreviewWrap.hidden = true;
  generateButton.disabled = true;
  notify('Screenshot removed.');
});

segButtons.forEach((btn) => btn.addEventListener('click', () => {
  segButtons.forEach((b) => b.classList.toggle('active', b === btn));
  previewIframe.style.width = btn.dataset.width;
}));

['dragenter', 'dragover'].forEach((name) => dropZone?.addEventListener(name, (event) => {
  event.preventDefault();
  dropZone.classList.add('dragging');
}));
['dragleave', 'drop'].forEach((name) => dropZone?.addEventListener(name, (event) => {
  event.preventDefault();
  dropZone.classList.remove('dragging');
  if (event.type === 'drop') upload(event.dataTransfer.files[0]);
}));

async function generateWebpage() {
  if (!uploadedImageUrl) return notify('Upload a screenshot first.', true);
  resultCard.hidden = false;
  setGenerating(true);
  resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    const response = await fetch('/webpage/generate', { method: 'POST' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Generation failed.');

    currentHtml = payload.html;
    currentCss = payload.css;
    htmlEditor.value = currentHtml;
    cssEditor.value = currentCss;

    previewIframe.srcdoc = buildPreviewDoc(currentHtml, currentCss);

    switchTab('preview');
    notify(payload.method === 'fallback'
      ? 'Generated with text analysis (no vision model on this account).'
      : 'HTML and CSS generated successfully.');
  } catch (error) {
    notify(error.message, true);
  } finally {
    setGenerating(false);
  }
}

// Merge HTML+CSS for preview only: swap the stylesheet link for an inline <style>.
function buildPreviewDoc(html, css) {
  const styleTag = `<style>\n${css}\n</style>`;
  if (/<html/i.test(html)) {
    if (/<link[^>]*stylesheet[^>]*>/i.test(html)) {
      return html.replace(/<link[^>]*stylesheet[^>]*>/i, styleTag);
    }
    if (/<\/head>/i.test(html)) {
      return html.replace(/<\/head>/i, `${styleTag}</head>`);
    }
    return styleTag + html;
  }
  return `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">${styleTag}</head>
<body>${html}</body>
</html>`;
}

generateButton?.addEventListener('click', generateWebpage);

document.querySelector('#copy-html')?.addEventListener('click', async () => {
  if (!currentHtml) return notify('No HTML generated yet.', true);
  await navigator.clipboard.writeText(currentHtml);
  notify('HTML copied to clipboard.');
});

document.querySelector('#copy-css')?.addEventListener('click', async () => {
  if (!currentCss) return notify('No CSS generated yet.', true);
  await navigator.clipboard.writeText(currentCss);
  notify('CSS copied to clipboard.');
});

document.querySelector('#download-zip')?.addEventListener('click', async () => {
  if (!currentHtml || !currentCss) return notify('Generate a webpage first.', true);
  if (typeof JSZip === 'undefined') return notify('ZIP library not loaded.', true);

  const zip = new JSZip();
  const indexHtml = /<html/i.test(currentHtml)
    ? currentHtml
    : `<!doctype html>\n<html lang="en">\n<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Generated Page</title><link rel="stylesheet" href="style.css"></head>\n<body>\n${currentHtml}\n</body>\n</html>`;
  zip.file('index.html', indexHtml);
  zip.file('style.css', currentCss);
  const blob = await zip.generateAsync({ type: 'blob' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'generated-webpage.zip';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  notify('ZIP downloaded.');
});
