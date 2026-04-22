"""
ENTROPIA - servidor HTTP (Flask).

Hospeda personagens, bestiario e imagens da mesa, com autenticacao por
usuario. Destinado a rodar num VPS via gunicorn; para dev local basta
`python servidor.py`.

Bootstrap de usuarios (uma vez por jogador):
    python servidor.py criar-usuario

Rodar em dev:
    python servidor.py

Rodar em producao (ver README_DEPLOY.md):
    gunicorn --workers 1 --bind 127.0.0.1:5000 servidor:app
"""

import getpass
import json
import os
import secrets
import sys
import time
import uuid
from datetime import datetime
from functools import wraps

import bcrypt
from flask import Flask, g, jsonify, request, send_from_directory

# =============================================================================
# LAYOUT EM DISCO
# =============================================================================

PASTA_SERVIDOR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.environ.get("ENTROPIA_DADOS_DIR") or os.path.join(PASTA_SERVIDOR, "dados")

ARQUIVO_USUARIOS = os.path.join(DADOS_DIR, "usuarios.json")
ARQUIVO_PERSONAGENS = os.path.join(DADOS_DIR, "personagens.json")
ARQUIVO_BESTIARIO = os.path.join(DADOS_DIR, "bestiario.json")
ARQUIVO_HABILIDADES = os.path.join(DADOS_DIR, "habilidades.json")
PASTA_IMAGENS = os.path.join(DADOS_DIR, "imagens")


def _garantir_estrutura():
    os.makedirs(DADOS_DIR, exist_ok=True)
    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    for caminho, conteudo in (
        (ARQUIVO_USUARIOS, {"usuarios": []}),
        (ARQUIVO_PERSONAGENS, {"personagens": []}),
        (ARQUIVO_BESTIARIO, {"monstros": []}),
        (ARQUIVO_HABILIDADES, {"habilidades": []}),
    ):
        if not os.path.exists(caminho):
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(conteudo, f, ensure_ascii=False, indent=2)


def _ler_json(caminho, chave):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f).get(chave, [])
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _gravar_json(caminho, chave, valor):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({chave: valor}, f, ensure_ascii=False, indent=2)


def carregar_usuarios():
    return _ler_json(ARQUIVO_USUARIOS, "usuarios")


def gravar_usuarios(usuarios):
    _gravar_json(ARQUIVO_USUARIOS, "usuarios", usuarios)


def carregar_personagens():
    return _ler_json(ARQUIVO_PERSONAGENS, "personagens")


def gravar_personagens(personagens):
    _gravar_json(ARQUIVO_PERSONAGENS, "personagens", personagens)


def carregar_bestiario():
    return _ler_json(ARQUIVO_BESTIARIO, "monstros")


def gravar_bestiario(monstros):
    _gravar_json(ARQUIVO_BESTIARIO, "monstros", monstros)


def carregar_habilidades():
    return _ler_json(ARQUIVO_HABILIDADES, "habilidades")


def gravar_habilidades(habilidades):
    _gravar_json(ARQUIVO_HABILIDADES, "habilidades", habilidades)


# =============================================================================
# TOKENS EM MEMORIA
# -----------------------------------------------------------------------------
# TTL de 24h. Restart do servidor invalida tudo (aceito na V1).
# =============================================================================

TOKEN_TTL_SEGUNDOS = 24 * 3600
_TOKENS = {}  # token -> {"usuario", "papel", "expira_em"}


def _novo_token(usuario, papel):
    token = secrets.token_urlsafe(32)
    _TOKENS[token] = {
        "usuario": usuario,
        "papel": papel,
        "expira_em": time.time() + TOKEN_TTL_SEGUNDOS,
    }
    return token


def _invalidar_token(token):
    _TOKENS.pop(token, None)


def _resolver_token(token):
    info = _TOKENS.get(token)
    if not info:
        return None
    if info["expira_em"] < time.time():
        _TOKENS.pop(token, None)
        return None
    return info


# =============================================================================
# AUTH
# =============================================================================


def _hash(texto):
    return bcrypt.hashpw(texto.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _confere_hash(texto, hashed):
    try:
        return bcrypt.checkpw(texto.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _encontrar_usuario(nome):
    alvo = nome.casefold()
    for u in carregar_usuarios():
        if str(u.get("usuario", "")).casefold() == alvo:
            return u
    return None


def autenticado(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Auth-Token", "")
        info = _resolver_token(token)
        if not info:
            return jsonify({"erro": "token invalido ou expirado"}), 401
        g.usuario = info["usuario"]
        g.papel = info["papel"]
        g.token = token
        return func(*args, **kwargs)

    return wrapper


def exige_mestre(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if str(g.papel).casefold() != "mestre":
            return jsonify({"erro": "apenas o mestre pode acessar"}), 403
        return func(*args, **kwargs)

    return wrapper


# =============================================================================
# APP FLASK
# =============================================================================

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB por request (uploads)


@app.before_request
def _preparar():
    _garantir_estrutura()


# ----- login -----

@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json(silent=True) or {}
    usuario = str(dados.get("usuario", "")).strip()
    senha = str(dados.get("senha", ""))
    palavra_chave = str(dados.get("palavra_chave", ""))

    if not usuario or not senha or not palavra_chave:
        return jsonify({"erro": "usuario, senha e palavra_chave sao obrigatorios"}), 400

    registro = _encontrar_usuario(usuario)
    if not registro:
        return jsonify({"erro": "usuario nao encontrado"}), 401
    if not _confere_hash(senha, registro.get("senha_hash", "")):
        return jsonify({"erro": "senha incorreta"}), 401
    if not _confere_hash(palavra_chave.casefold(), registro.get("palavra_hash", "")):
        return jsonify({"erro": "palavra-chave incorreta"}), 401

    papel = registro.get("papel", "jogador")
    token = _novo_token(registro["usuario"], papel)
    return jsonify({
        "token": token,
        "usuario": registro["usuario"],
        "papel": papel,
    })


@app.route("/logout", methods=["POST"])
@autenticado
def logout():
    _invalidar_token(g.token)
    return "", 204


# ----- personagens -----

def _eh_mestre():
    return str(g.papel).casefold() == "mestre"


@app.route("/personagens", methods=["GET"])
@autenticado
def listar_personagens():
    todos = carregar_personagens()
    if _eh_mestre():
        return jsonify(todos)
    alvo = g.usuario.casefold()
    meus = [p for p in todos if str(p.get("criado_por", "")).casefold() == alvo]
    return jsonify(meus)


@app.route("/personagens", methods=["POST"])
@autenticado
def criar_personagem():
    personagem = request.get_json(silent=True) or {}
    # server e autoridade sobre estas 3 chaves:
    personagem["id"] = personagem.get("id") or uuid.uuid4().hex
    personagem["criado_por"] = g.usuario
    personagem["criado_em"] = datetime.now().strftime("%d/%m/%y")
    lista = carregar_personagens()
    lista.append(personagem)
    gravar_personagens(lista)
    return jsonify(personagem), 201


@app.route("/personagens/<personagem_id>", methods=["PUT"])
@autenticado
def atualizar_personagem(personagem_id):
    body = request.get_json(silent=True) or {}
    lista = carregar_personagens()
    for i, p in enumerate(lista):
        if p.get("id") == personagem_id:
            dono = str(p.get("criado_por", "")).casefold()
            if dono != g.usuario.casefold() and not _eh_mestre():
                return jsonify({"erro": "sem permissao"}), 403
            # preserva criado_por / criado_em / id do servidor
            body["id"] = p.get("id")
            body["criado_por"] = p.get("criado_por")
            body["criado_em"] = p.get("criado_em")
            lista[i] = body
            gravar_personagens(lista)
            return "", 204
    return jsonify({"erro": "personagem nao encontrado"}), 404


@app.route("/personagens/<personagem_id>", methods=["DELETE"])
@autenticado
def deletar_personagem(personagem_id):
    lista = carregar_personagens()
    alvo = next((p for p in lista if p.get("id") == personagem_id), None)
    if not alvo:
        return jsonify({"erro": "personagem nao encontrado"}), 404
    dono = str(alvo.get("criado_por", "")).casefold()
    if dono != g.usuario.casefold() and not _eh_mestre():
        return jsonify({"erro": "sem permissao"}), 403
    gravar_personagens([p for p in lista if p.get("id") != personagem_id])
    return "", 204


# ----- bestiario (apenas mestre) -----

@app.route("/bestiario", methods=["GET"])
@autenticado
@exige_mestre
def listar_bestiario():
    return jsonify(carregar_bestiario())


@app.route("/bestiario", methods=["PUT"])
@autenticado
@exige_mestre
def substituir_bestiario():
    body = request.get_json(silent=True)
    if not isinstance(body, list):
        return jsonify({"erro": "body deve ser uma lista de monstros"}), 400
    gravar_bestiario(body)
    return "", 204


# ----- habilidades (catalogo compartilhado, qualquer usuario autenticado) -----

@app.route("/habilidades", methods=["GET"])
@autenticado
def listar_habilidades():
    return jsonify(carregar_habilidades())


@app.route("/habilidades", methods=["POST"])
@autenticado
def criar_habilidade():
    body = request.get_json(silent=True) or {}
    nome = str(body.get("nome", "")).strip()
    if not nome:
        return jsonify({"erro": "nome obrigatorio"}), 400
    habilidade = {
        "id": body.get("id") or uuid.uuid4().hex,
        "nome": nome,
        "descricao": str(body.get("descricao", "")).strip(),
        "criado_por": g.usuario,
        "criado_em": datetime.now().strftime("%d/%m/%y"),
    }
    lista = carregar_habilidades()
    lista.append(habilidade)
    gravar_habilidades(lista)
    return jsonify(habilidade), 201


# ----- imagens -----

EXTENSOES_PERMITIDAS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


@app.route("/imagens", methods=["POST"])
@autenticado
def upload_imagem():
    if "file" not in request.files:
        return jsonify({"erro": "envie o arquivo no campo 'file' multipart"}), 400
    arquivo = request.files["file"]
    if not arquivo or not arquivo.filename:
        return jsonify({"erro": "arquivo vazio"}), 400
    extensao = os.path.splitext(arquivo.filename)[1].lower() or ".png"
    if extensao not in EXTENSOES_PERMITIDAS:
        return jsonify({"erro": f"extensao '{extensao}' nao suportada"}), 400
    nome = f"{uuid.uuid4().hex}{extensao}"
    destino = os.path.join(PASTA_IMAGENS, nome)
    arquivo.save(destino)
    return jsonify({"nome": nome}), 201


@app.route("/imagens/<nome>", methods=["GET"])
@autenticado
def baixar_imagem(nome):
    nome_seguro = os.path.basename(nome)
    caminho = os.path.join(PASTA_IMAGENS, nome_seguro)
    if not os.path.exists(caminho):
        return jsonify({"erro": "imagem nao encontrada"}), 404
    return send_from_directory(PASTA_IMAGENS, nome_seguro)


# ----- util -----

@app.route("/saude", methods=["GET"])
def saude():
    return jsonify({"ok": True, "dados_dir": DADOS_DIR})


# =============================================================================
# CLI — criar/listar usuarios
# =============================================================================


def cmd_criar_usuario():
    _garantir_estrutura()
    print("=== Criar usuario ENTROPIA ===")
    usuario = input("Usuario: ").strip()
    if not usuario:
        print("usuario vazio, cancelando.")
        return 1
    if _encontrar_usuario(usuario):
        print(f"ja existe um usuario '{usuario}'.")
        return 1
    senha = getpass.getpass("Senha: ")
    if not senha:
        print("senha vazia, cancelando.")
        return 1
    palavra = getpass.getpass("Palavra-chave: ").strip()
    if not palavra:
        print("palavra-chave vazia, cancelando.")
        return 1
    papel = input("Papel (mestre/jogador) [jogador]: ").strip().lower() or "jogador"
    if papel not in {"mestre", "jogador"}:
        print("papel invalido, use 'mestre' ou 'jogador'.")
        return 1

    usuarios = carregar_usuarios()
    usuarios.append({
        "usuario": usuario,
        "senha_hash": _hash(senha),
        "palavra_hash": _hash(palavra.casefold()),
        "papel": papel,
    })
    gravar_usuarios(usuarios)
    print(f"usuario '{usuario}' criado ({papel}).")
    return 0


def cmd_listar_usuarios():
    _garantir_estrutura()
    usuarios = carregar_usuarios()
    if not usuarios:
        print("(nenhum usuario cadastrado)")
        return 0
    for u in usuarios:
        print(f"  {u.get('usuario'):20s}  {u.get('papel')}")
    return 0


def cmd_remover_usuario():
    _garantir_estrutura()
    nome = input("Usuario a remover: ").strip()
    registro = _encontrar_usuario(nome)
    if not registro:
        print("usuario nao encontrado.")
        return 1
    confirma = input(f"remover '{registro['usuario']}'? [s/N]: ").strip().lower()
    if confirma != "s":
        print("cancelado.")
        return 0
    usuarios = [u for u in carregar_usuarios() if u is not registro and
                str(u.get("usuario", "")).casefold() != str(registro.get("usuario", "")).casefold()]
    gravar_usuarios(usuarios)
    print(f"usuario '{registro['usuario']}' removido.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        if comando == "criar-usuario":
            sys.exit(cmd_criar_usuario())
        if comando == "listar-usuarios":
            sys.exit(cmd_listar_usuarios())
        if comando == "remover-usuario":
            sys.exit(cmd_remover_usuario())
        print(f"comando desconhecido: {comando}")
        print("uso: python servidor.py [criar-usuario|listar-usuarios|remover-usuario]")
        sys.exit(2)
    _garantir_estrutura()
    app.run(host="0.0.0.0", port=5000, debug=False)
