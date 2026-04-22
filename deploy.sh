#!/usr/bin/env bash
# ENTROPIA - sobe o servidor Flask/gunicorn na porta 3013.
# Roda como seu proprio usuario (SEM sudo, SEM apt, SEM chown).
# Assume que python3 + venv ja estao instalados no VPS.
#
# Uso:
#   bash deploy.sh

set -euo pipefail

PORTA=3013
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DADOS_DIR="$APP_DIR/dados"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

command -v python3 >/dev/null || { echo "python3 nao encontrado. peca pro admin instalar."; exit 1; }

echo "[entropia] normalizando line endings..."
for f in "$APP_DIR"/*.py "$APP_DIR"/*.sh "$APP_DIR"/*.txt; do
  [[ -f "$f" ]] && sed -i 's/\r$//' "$f" || true
done

echo "[entropia] criando venv em $APP_DIR/venv..."
if [[ -d "$APP_DIR/venv" && ! -x "$APP_DIR/venv/bin/pip" ]]; then
  echo "[entropia] venv existente esta quebrado, removendo..."
  rm -rf "$APP_DIR/venv"
fi
if [[ ! -d "$APP_DIR/venv" ]]; then
  if ! python3 -m venv "$APP_DIR/venv" 2>/dev/null; then
    echo
    echo "ERRO: 'python3 -m venv' falhou. o pacote python3-venv provavelmente"
    echo "      nao esta instalado. peca pro admin do VPS rodar (uma vez so):"
    echo
    echo "        sudo apt-get install -y python3-venv python3-pip"
    echo
    rm -rf "$APP_DIR/venv"
    exit 1
  fi
fi
"$APP_DIR/venv/bin/pip" install --upgrade pip >/dev/null
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "[entropia] preparando $DADOS_DIR..."
mkdir -p "$DADOS_DIR/imagens"

echo "[entropia] escrevendo service systemd (modo --user)..."
mkdir -p "$SYSTEMD_USER_DIR"
cat > "$SYSTEMD_USER_DIR/entropia.service" <<EOF
[Unit]
Description=ENTROPIA server
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment="ENTROPIA_DADOS_DIR=$DADOS_DIR"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 1 --bind 127.0.0.1:$PORTA --access-logfile - --error-logfile - servidor:app
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable entropia
systemctl --user restart entropia
sleep 1

if systemctl --user is-active --quiet entropia; then
  echo "[entropia] OK - rodando em 127.0.0.1:$PORTA"
  echo
  echo "proximos passos:"
  echo "  1) criar usuarios:"
  echo "       ENTROPIA_DADOS_DIR=$DADOS_DIR $APP_DIR/venv/bin/python $APP_DIR/servidor.py criar-usuario"
  echo "  2) testar:"
  echo "       curl http://127.0.0.1:$PORTA/saude"
  echo "  3) no painel, apontar o proxy do dominio pra 127.0.0.1:$PORTA"
  echo "  4) logs: journalctl --user -u entropia -f"
  echo
  echo "DICA: pra manter rodando mesmo com voce deslogado, peca ao admin uma vez:"
  echo "       sudo loginctl enable-linger $USER"
else
  echo "[entropia] ERRO - service nao subiu"
  journalctl --user -u entropia -n 30 --no-pager || true
  exit 1
fi
