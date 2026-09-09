document.querySelectorAll('pre').forEach((block) => {
  const toolbar = document.createElement('div');
  toolbar.className = 'code-toolbar';
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'copy';
  button.textContent = 'Copiar código';
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(block.innerText);
      document.getElementById('copy-status').textContent = 'Código copiado.';
      button.textContent = 'Copiado';
      setTimeout(() => { button.textContent = 'Copiar código'; }, 1800);
    } catch {
      document.getElementById('copy-status').textContent = 'Selecione o código e copie manualmente.';
    }
  });
  toolbar.appendChild(button);
  block.after(toolbar);
});
