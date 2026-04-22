# Deploy do servidor ENTROPIA

Este guia cobre: subir o `servidor.py` num VPS Linux, criar usuários, e apontar o cliente Tkinter pra ele.

---

## 1. No VPS (Ubuntu/Debian)

```bash
sudo mkdir -p /opt/entropia
sudo chown $USER:$USER /opt/entropia
cd /opt/entropia

# subir os arquivos do projeto (via git clone, scp, rsync, etc)
# no minimo: servidor.py e requirements.txt
git clone <seu-repo> .

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p dados/imagens
```

Estrutura no servidor após setup:

```
/opt/entropia/
├── servidor.py
├── requirements.txt
├── venv/
└── dados/
    ├── usuarios.json      # criado no primeiro uso
    ├── personagens.json
    ├── bestiario.json
    └── imagens/
```

Se quiser guardar os dados em outro lugar (ex: `/var/lib/entropia`), exporte:

```bash
export ENTROPIA_DADOS_DIR=/var/lib/entropia
```

---

## 2. Criar os usuários

Rode uma vez por jogador (inclusive o próprio mestre):

```bash
python servidor.py criar-usuario
# Prompt interativo: usuario, senha, palavra-chave, papel (mestre/jogador)
```

Outros comandos úteis:

```bash
python servidor.py listar-usuarios
python servidor.py remover-usuario
```

Senhas e palavras-chave são armazenadas hasheadas com bcrypt em `dados/usuarios.json` — seguras mesmo se o arquivo vazar.

---

## 3. Testar em dev (primeira vez)

```bash
python servidor.py     # sobe em http://0.0.0.0:5000
```

Em outra janela:

```bash
# login
curl -X POST http://localhost:5000/login \
     -H 'Content-Type: application/json' \
     -d '{"usuario":"O MESTRE","senha":"...","palavra_chave":"..."}'

# deve devolver {"token":"...","usuario":"O MESTRE","papel":"mestre"}

TOKEN=<cole o token>

curl -H "X-Auth-Token: $TOKEN" http://localhost:5000/personagens
curl -H "X-Auth-Token: $TOKEN" http://localhost:5000/saude
```

---

## 4. Produção com Gunicorn + systemd

### 4a. Unit file

Crie `/etc/systemd/system/entropia.service`:

```ini
[Unit]
Description=ENTROPIA server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/entropia
Environment="ENTROPIA_DADOS_DIR=/opt/entropia/dados"
ExecStart=/opt/entropia/venv/bin/gunicorn \
    --workers 1 \
    --bind 127.0.0.1:5000 \
    --access-logfile - \
    --error-logfile - \
    servidor:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **`--workers 1`** é intencional: a V1 grava JSONs direto no disco sem lock, então vários workers podem corromper o arquivo em escritas simultâneas. Um worker só suporta vários jogadores na mesma mesa tranquilamente.

### 4b. Permissões e ativação

```bash
sudo chown -R www-data:www-data /opt/entropia/dados
sudo systemctl daemon-reload
sudo systemctl enable --now entropia
sudo systemctl status entropia
sudo journalctl -u entropia -f    # logs em tempo real
```

---

## 5. Nginx + HTTPS (recomendado)

Expor direto na porta 5000 sem TLS funciona pra testar, mas pra produção:

```nginx
# /etc/nginx/sites-available/entropia
server {
    listen 80;
    server_name entropia.seudominio.com;

    client_max_body_size 20M;    # uploads de imagem

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/entropia /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d entropia.seudominio.com
```

Agora o servidor está em `https://entropia.seudominio.com`.

---

## 6. Configurar o cliente

Em cada máquina que vai rodar o cliente Tkinter, edite o `app.json` (está ao lado do `entropia.py`):

```json
{
  "modo": "remoto",
  "servidor_url": "https://entropia.seudominio.com",
  "token": null,
  "usuario": null
}
```

Se o arquivo não existir, rode o cliente uma vez — ele cria o `app.json` em modo local por padrão. Depois edite para `"remoto"`.

Para voltar ao modo local (offline, arquivos na própria máquina):

```json
{ "modo": "local" }
```

Os dois modos coexistem no mesmo código — você só muda o `app.json`.

---

## 7. Distribuindo o cliente pros jogadores

Três caminhos:

1. **Python + requirements** (mais simples): mandar a pasta do projeto + `requirements.txt` e instruir:
   ```bash
   pip install -r requirements.txt
   python entropia.py
   ```

2. **PyInstaller** (zero instalação pros jogadores):
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --windowed --name entropia entropia.py
   # gera dist/entropia.exe (Windows) ou dist/entropia (Linux/Mac)
   ```
   Junto com o `.exe`, distribua um `app.json` já configurado apontando pro seu servidor.

3. **GitHub** — commit público ou privado; jogadores clonam e rodam.

---

## 8. Manutenção

### Atualizar o servidor

```bash
cd /opt/entropia
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart entropia
```

> Restart invalida todos os tokens ativos — os jogadores precisarão fazer login de novo (é só reabrir o cliente).

### Backup

A única coisa que precisa de backup é `/opt/entropia/dados/`. Um `tar -czf` diário via cron resolve:

```bash
0 3 * * *  tar -czf /var/backups/entropia-$(date +\%F).tar.gz -C /opt/entropia dados
```

---

## 9. Limitações conhecidas (V1)

- **1 worker no gunicorn**: escritas simultâneas podem corromper JSONs. Mitigação natural: uma mesa ativa raramente tem mais de 1 request/segundo.
- **Tokens em memória**: restart do servidor força re-login. Aceitável pra mesa caseira.
- **Sem sync em tempo real**: se o Mestre muda o HP de um monstro, os jogadores só veem depois de recarregar o cliente. Próximo passo do roadmap é adicionar WebSocket.
- **Sem HTTPS fora do nginx**: o Flask dev server (`python servidor.py`) serve HTTP puro. Use nginx + certbot na produção.
