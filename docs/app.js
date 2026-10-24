document.querySelectorAll('.code-window').forEach((frame) => {
  const code = frame.querySelector('pre code');
  const toolbar = document.createElement('div');
  toolbar.className = 'code-toolbar';
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'copy';
  const label = frame.classList.contains('terminal') ? 'Copiar texto' : 'Copiar código';
  button.textContent = label;
  button.setAttribute('aria-label', `${label}: ${frame.querySelector('.window-title').textContent}`);
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(code.textContent);
      document.getElementById('copy-status').textContent = 'Texto copiado.';
      button.textContent = 'Copiado';
      setTimeout(() => { button.textContent = label; }, 1800);
    } catch {
      document.getElementById('copy-status').textContent = 'Selecione o texto e copie manualmente.';
    }
  });
  toolbar.appendChild(button);
  frame.appendChild(toolbar);
});
