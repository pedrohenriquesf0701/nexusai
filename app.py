from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
import os
import re
import base64

app = Flask(__name__)
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def md_to_html(text):
    blocos = {}
    def salvar_bloco(m):
        key = f"BLOCO{len(blocos)}"
        blocos[key] = f'<pre><code>{m.group(1).strip()}</code></pre>'
        return key
    text = re.sub(r'```(?:\w+)?\n?(.*?)```', salvar_bloco, text, flags=re.DOTALL)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^\* (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'\n\n+', '</p><p>', text)
    text = f'<p>{text}</p>'
    for key, val in blocos.items():
        text = text.replace(key, val)
    return text

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NexusAI — Converse com inteligência</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #080810;
    --surface: #10101e;
    --surface2: #16162a;
    --border: rgba(255,255,255,0.07);
    --accent: #7c6af7;
    --accent2: #f76a8c;
    --text: #e8e8f0;
    --muted: #6b6b88;
    --user-bubble: #1e1e38;
    --ai-bubble: #13132a;
    --glow: rgba(124,106,247,0.15);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  body::before, body::after {
    content: '';
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
  }
  body::before {
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(124,106,247,0.12), transparent);
    top: -100px; left: -100px;
  }
  body::after {
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(247,106,140,0.08), transparent);
    bottom: -80px; right: -80px;
  }

  header {
    position: relative; z-index: 10;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    background: rgba(8,8,16,0.8);
    backdrop-filter: blur(20px);
  }

  .logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 22px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .badge {
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
    border: 1px solid var(--border);
    color: var(--muted);
    background: var(--surface);
  }

  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 32px 0;
    position: relative;
    z-index: 1;
    scroll-behavior: smooth;
  }

  #chat::-webkit-scrollbar { width: 4px; }
  #chat::-webkit-scrollbar-track { background: transparent; }
  #chat::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  .msg-wrap {
    max-width: 760px;
    margin: 0 auto 24px;
    padding: 0 24px;
    animation: fadeUp 0.3s ease;
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .msg { display: flex; gap: 14px; align-items: flex-start; }
  .msg.user { flex-direction: row-reverse; }

  .avatar {
    width: 36px; height: 36px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
  }

  .avatar.ai {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    box-shadow: 0 0 20px var(--glow);
  }

  .avatar.user {
    background: var(--surface2);
    border: 1px solid var(--border);
  }

  .bubble {
    max-width: 80%;
    padding: 14px 18px;
    border-radius: 16px;
    line-height: 1.7;
    font-size: 15px;
  }

  .msg.ai .bubble {
    background: var(--ai-bubble);
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
  }

  .msg.user .bubble {
    background: var(--user-bubble);
    border: 1px solid rgba(124,106,247,0.2);
    border-top-right-radius: 4px;
    color: #c8c8e8;
  }

  .bubble h1, .bubble h2, .bubble h3 { font-family: 'Syne', sans-serif; margin: 12px 0 6px; color: #fff; }
  .bubble h3 { font-size: 15px; }
  .bubble strong { color: #fff; }
  .bubble code { background: rgba(124,106,247,0.15); padding: 2px 6px; border-radius: 4px; font-size: 13px; color: #b4aaff; font-family: monospace; }
  .bubble pre { background: rgba(0,0,0,0.4); border: 1px solid var(--border); border-radius: 8px; padding: 14px; overflow-x: auto; margin: 10px 0; }
  .bubble pre code { background: transparent; padding: 0; color: #a8ff78; font-size: 13px; }
  .bubble ul { padding-left: 20px; margin: 8px 0; }
  .bubble li { margin: 4px 0; }
  .bubble p { margin: 6px 0; }
  .bubble img { max-width: 100%; border-radius: 8px; margin: 8px 0; }

  #welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    padding: 40px;
  }

  .welcome-icon { font-size: 48px; margin-bottom: 20px; animation: float 3s ease-in-out infinite; }

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
  }

  #welcome h2 {
    font-family: 'Syne', sans-serif;
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #fff, var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  #welcome p { color: var(--muted); font-size: 16px; max-width: 400px; line-height: 1.6; }

  .suggestions { display: flex; gap: 10px; margin-top: 28px; flex-wrap: wrap; justify-content: center; }

  .suggestion {
    padding: 10px 16px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--muted);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .suggestion:hover { border-color: var(--accent); color: var(--text); background: var(--surface2); }

  footer {
    position: relative; z-index: 10;
    padding: 12px 24px 20px;
    background: rgba(8,8,16,0.9);
    backdrop-filter: blur(20px);
    border-top: 1px solid var(--border);
  }

  /* File preview */
  #file-preview {
    max-width: 760px;
    margin: 0 auto 8px;
    display: none;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
  }

  #file-preview.show { display: flex; }

  .file-icon { font-size: 20px; }

  .file-name { font-size: 13px; color: var(--text); flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .file-remove {
    background: none;
    border: none;
    color: var(--muted);
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
    padding: 0 4px;
  }

  .file-remove:hover { color: var(--accent2); }

  .input-wrap {
    max-width: 760px;
    margin: 0 auto;
    display: flex;
    gap: 10px;
    align-items: flex-end;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 10px 12px;
    transition: border-color 0.2s;
  }

  .input-wrap:focus-within { border-color: rgba(124,106,247,0.4); box-shadow: 0 0 0 3px rgba(124,106,247,0.05); }

  #input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    resize: none;
    max-height: 120px;
    line-height: 1.5;
  }

  #input::placeholder { color: var(--muted); }

  #file-input { display: none; }

  .btn-icon {
    width: 36px; height: 36px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--surface2);
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: all 0.2s;
    font-size: 16px;
  }

  .btn-icon:hover { border-color: var(--accent); background: var(--surface); }

  #send {
    width: 36px; height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border: none;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: transform 0.15s, box-shadow 0.15s;
  }

  #send:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(124,106,247,0.4); }
  #send:active { transform: scale(0.97); }
  #send svg { width: 17px; height: 17px; fill: white; }

  .footer-note { text-align: center; font-size: 11px; color: var(--muted); margin-top: 8px; max-width: 760px; margin-left: auto; margin-right: auto; }

  .typing { display: flex; gap: 4px; align-items: center; padding: 14px 18px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); animation: bounce 1.2s infinite; }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }

  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-6px); background: var(--accent); }
  }

  .file-bubble {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(124,106,247,0.1);
    border: 1px solid rgba(124,106,247,0.2);
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #b4aaff;
  }
</style>
</head>
<body>

<header>
  <div class="logo">Nexus<span>AI</span></div>
  <div class="badge">✦ Powered by Gemini</div>
</header>

<div id="chat">
  <div id="welcome">
    <div class="welcome-icon">✦</div>
    <h2>Como posso te ajudar?</h2>
    <p>Faça qualquer pergunta ou envie um arquivo para analisar.</p>
    <div class="suggestions">
      <div class="suggestion" onclick="suggest(this)">💡 Me explica machine learning</div>
      <div class="suggestion" onclick="suggest(this)">🐍 Como aprender Python rápido?</div>
      <div class="suggestion" onclick="suggest(this)">🚀 Ideias de projetos com IA</div>
      <div class="suggestion" onclick="suggest(this)">💸 Como ganhar dinheiro com código</div>
    </div>
  </div>
</div>

<footer>
  <div id="file-preview">
    <span class="file-icon">📎</span>
    <span class="file-name" id="file-name-text"></span>
    <button class="file-remove" onclick="removeFile()">×</button>
  </div>
  <div class="input-wrap">
    <button class="btn-icon" onclick="document.getElementById('file-input').click()" title="Anexar arquivo">📎</button>
    <input type="file" id="file-input" accept="image/*,.pdf,.txt,.py,.js,.html,.css,.json,.csv" onchange="handleFile(this)">
    <textarea id="input" rows="1" placeholder="Manda sua pergunta..."></textarea>
    <button id="send" onclick="send()">
      <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
    </button>
  </div>
  <div class="footer-note">NexusAI pode cometer erros. Suporta imagens, PDF e arquivos de texto.</div>
</footer>

<script>
  const chat = document.getElementById('chat');
  const input = document.getElementById('input');
  const welcome = document.getElementById('welcome');
  let history = [];
  let currentFile = null;

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  function suggest(el) {
    input.value = el.textContent.slice(2).trim();
    send();
  }

  function handleFile(input) {
    const file = input.files[0];
    if (!file) return;
    currentFile = file;
    document.getElementById('file-name-text').textContent = file.name;
    document.getElementById('file-preview').classList.add('show');
  }

  function removeFile() {
    currentFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-preview').classList.remove('show');
  }

  function getFileIcon(name) {
    if (/\.(jpg|jpeg|png|gif|webp)$/i.test(name)) return '🖼️';
    if (/\.pdf$/i.test(name)) return '📄';
    if (/\.(py|js|html|css|json)$/i.test(name)) return '💻';
    if (/\.csv$/i.test(name)) return '📊';
    return '📎';
  }

  function addMsg(role, html, fileName) {
    welcome.style.display = 'none';
    const wrap = document.createElement('div');
    wrap.className = 'msg-wrap';
    const fileHtml = fileName ? `<div class="file-bubble">${getFileIcon(fileName)} ${fileName}</div>` : '';
    wrap.innerHTML = `
      <div class="msg ${role}">
        <div class="avatar ${role}">${role === 'ai' ? '✦' : '👤'}</div>
        <div class="bubble">${role === 'user' ? fileHtml : ''}${html}</div>
      </div>`;
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
    return wrap;
  }

  async function send() {
    const text = input.value.trim();
    if (!text && !currentFile) return;

    const file = currentFile;
    const fileName = file ? file.name : null;

    input.value = '';
    input.style.height = 'auto';
    removeFile();

    addMsg('user', text || '<em>Arquivo enviado</em>', fileName);
    history.push({ role: 'user', content: text });

    const typingWrap = addMsg('ai', '<div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>');

    try {
      let body;
      if (file) {
        const formData = new FormData();
        formData.append('message', text);
        formData.append('history', JSON.stringify(history));
        formData.append('file', file);
        const res = await fetch('/chat', { method: 'POST', body: formData });
        const data = await res.json();
        typingWrap.querySelector('.bubble').innerHTML = data.html;
        history.push({ role: 'assistant', content: data.text });
      } else {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ history })
        });
        const data = await res.json();
        typingWrap.querySelector('.bubble').innerHTML = data.html;
        history.push({ role: 'assistant', content: data.text });
      }
    } catch(e) {
      typingWrap.querySelector('.bubble').innerHTML = '<em>Erro ao conectar. Tente novamente.</em>';
    }

    chat.scrollTop = chat.scrollHeight;
  }
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    # Com arquivo
    if request.content_type and 'multipart/form-data' in request.content_type:
        import json
        message = request.form.get("message", "")
        history = json.loads(request.form.get("history", "[]"))
        file = request.files.get("file")

        contents = []

        # Histórico anterior
        for msg in history[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Mensagem atual com arquivo
        parts = []
        if file:
            file_bytes = file.read()
            mime_type = file.content_type or "application/octet-stream"

            if mime_type.startswith("image/"):
                parts.append({"inline_data": {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode()}})
            elif mime_type == "application/pdf":
                parts.append({"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(file_bytes).decode()}})
            else:
                # Texto puro
                try:
                    parts.append({"text": f"Arquivo '{file.filename}':\n\n{file_bytes.decode('utf-8')}"})
                except:
                    parts.append({"text": f"Arquivo '{file.filename}' enviado (binário)."})

        if message:
            parts.append({"text": message})
        else:
            parts.append({"text": "Analise este arquivo."})

        contents.append({"role": "user", "parts": parts})

    else:
        # Só texto
        data = request.json
        history = data.get("history", [])
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents
    )
    text = response.text
    return jsonify({"text": text, "html": md_to_html(text)})

if __name__ == "__main__":
    app.run(debug=True)