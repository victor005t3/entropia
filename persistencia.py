"""
ENTROPIA - camada de persistencia.

Expoe a mesma API independentemente do modo (local ou remoto) lido do
app.json. Em modo local le/escreve JSON na pasta do projeto; em modo
remoto fala com servidor.py via HTTP (ver README_DEPLOY.md).

Assinaturas estaveis (o resto do app importa destas):
    - login(usuario, senha, palavra_chave) -> (usuario_canonico, papel)
    - carregar_personagens, salvar_personagem,
      atualizar_personagem, remover_personagem
    - carregar_bestiario, salvar_bestiario
    - copiar_imagem(origem) -> id da imagem
    - caminho_imagem(id) -> path absoluto no disco (faz cache se remoto)
    - carregar_app_config / salvar_app_config
"""

import json
import os
import shutil
import sys
import uuid

try:
    import requests
except ImportError:
    requests = None  # modo local nao precisa; modo remoto vai falhar com mensagem clara


# =============================================================================
# ERROS
# =============================================================================


class ErroAutenticacao(Exception):
    """Credenciais invalidas. O atributo `campo` aponta o que falhou."""

    def __init__(self, motivo, campo=None):
        super().__init__(motivo)
        self.motivo = motivo
        self.campo = campo  # "usuario" | "senha" | "palavra_chave" | None


class ErroServidor(Exception):
    """Falha de rede ou resposta inesperada do servidor remoto."""


class ErroPermissao(Exception):
    """Usuario logado nao tem permissao pra operacao."""


# =============================================================================
# PATHS
# =============================================================================


if getattr(sys, "frozen", False):
    # Rodando dentro do .exe gerado pelo PyInstaller: dados persistentes
    # ficam ao lado do executavel; recursos read-only embutidos ficam
    # em sys._MEIPASS (pasta temporaria extraida no boot).
    PASTA_BASE = os.path.dirname(os.path.abspath(sys.executable))
    _PASTA_BUNDLE = getattr(sys, "_MEIPASS", PASTA_BASE)
else:
    PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
    _PASTA_BUNDLE = PASTA_BASE

ARQUIVO_CONFIG = os.path.join(PASTA_BASE, "app.json")
ARQUIVO_PERSONAGENS = os.path.join(PASTA_BASE, "personagens.json")
ARQUIVO_BESTIARIO = os.path.join(PASTA_BASE, "bestiario.json")
PASTA_IMAGENS = os.path.join(PASTA_BASE, "imagens")
PASTA_IMAGENS_CACHE = os.path.join(PASTA_BASE, "imagens_cache")
_ARQUIVO_CONFIG_BUNDLE = os.path.join(_PASTA_BUNDLE, "app.json")


# =============================================================================
# CONFIG (app.json)
# =============================================================================


_CONFIG_DEFAULT = {
    "modo": "local",
    "servidor_url": "",
    "token": None,
    "usuario": None,
}

_config_cache = None


def carregar_app_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not os.path.exists(ARQUIVO_CONFIG):
        # Primeira execucao: se ha um app.json embutido no bundle
        # (build do .exe), usa ele como template; senao cai no default.
        if (
            _ARQUIVO_CONFIG_BUNDLE != ARQUIVO_CONFIG
            and os.path.exists(_ARQUIVO_CONFIG_BUNDLE)
        ):
            try:
                with open(_ARQUIVO_CONFIG_BUNDLE, "r", encoding="utf-8") as f:
                    carregado = json.load(f) or {}
                _config_cache = dict(_CONFIG_DEFAULT)
                _config_cache.update(carregado)
                # Token e usuario nao devem vazar do template bundled.
                _config_cache["token"] = None
                _config_cache["usuario"] = None
            except (json.JSONDecodeError, OSError):
                _config_cache = dict(_CONFIG_DEFAULT)
        else:
            _config_cache = dict(_CONFIG_DEFAULT)
        try:
            _gravar_config(_config_cache)
        except OSError:
            pass
        return _config_cache

    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            carregado = json.load(f) or {}
    except (json.JSONDecodeError, OSError):
        carregado = {}

    _config_cache = dict(_CONFIG_DEFAULT)
    _config_cache.update(carregado)
    return _config_cache


def salvar_app_config(config):
    global _config_cache
    _config_cache = dict(_CONFIG_DEFAULT)
    _config_cache.update(config)
    _gravar_config(_config_cache)


def _gravar_config(config):
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _modo():
    return str(carregar_app_config().get("modo", "local")).lower()


def _servidor_url():
    return str(carregar_app_config().get("servidor_url", "")).rstrip("/")


def _token():
    return carregar_app_config().get("token")


# =============================================================================
# LOGIN
# =============================================================================


def login(usuario, senha, palavra_chave):
    """
    Valida credenciais e grava token + usuario canonico na config.
    Retorna (usuario_canonico, papel).
    Lanca ErroAutenticacao em caso de falha de credencial.
    """
    if _modo() == "remoto":
        return _login_remoto(usuario, senha, palavra_chave)
    return _login_local(usuario, senha, palavra_chave)


def _login_local(usuario, senha, palavra_chave):
    # Import tardio pra evitar ciclo — USUARIOS vive em entropia.py
    # porque o README instrui o usuario a edita-lo la.
    from entropia import USUARIOS

    usuario_norm = " ".join(usuario.split())
    dados = None
    canonico = None
    for nome, info in USUARIOS.items():
        if nome.casefold() == usuario_norm.casefold():
            dados = info
            canonico = nome
            break

    if dados is None:
        raise ErroAutenticacao("Usuario nao encontrado.", campo="usuario")
    if dados["senha"] != senha:
        raise ErroAutenticacao("Senha incorreta.", campo="senha")
    if dados["palavra_chave"].casefold() != palavra_chave.casefold():
        raise ErroAutenticacao("Palavra-chave incorreta.", campo="palavra_chave")

    cfg = carregar_app_config()
    cfg["usuario"] = canonico
    cfg["token"] = None  # modo local nao usa token
    salvar_app_config(cfg)

    return canonico, dados["papel"]


# =============================================================================
# PERSONAGENS
# =============================================================================


def carregar_personagens():
    if _modo() == "remoto":
        return _http_get("/personagens")
    return _carregar_personagens_local()


def salvar_personagem(personagem):
    if _modo() == "remoto":
        return _http_post("/personagens", json_body=personagem)
    personagens = _carregar_personagens_local()
    personagens.append(personagem)
    _gravar_personagens_local(personagens)
    return personagem


def atualizar_personagem(personagem):
    if _modo() == "remoto":
        status = _http_put(f"/personagens/{personagem['id']}", json_body=personagem)
        return status in (200, 204)
    personagens = _carregar_personagens_local()
    for i, p in enumerate(personagens):
        if p.get("id") == personagem.get("id"):
            personagens[i] = personagem
            _gravar_personagens_local(personagens)
            return True
    return False


def remover_personagem(personagem_id):
    if _modo() == "remoto":
        status = _http_delete(f"/personagens/{personagem_id}")
        return status in (200, 204)
    personagens = _carregar_personagens_local()
    novos = [p for p in personagens if p.get("id") != personagem_id]
    if len(novos) == len(personagens):
        return False
    _gravar_personagens_local(novos)
    return True


def _carregar_personagens_local():
    if not os.path.exists(ARQUIVO_PERSONAGENS):
        return []
    try:
        with open(ARQUIVO_PERSONAGENS, "r", encoding="utf-8") as f:
            return json.load(f).get("personagens", [])
    except (json.JSONDecodeError, OSError):
        return []


def _gravar_personagens_local(personagens):
    with open(ARQUIVO_PERSONAGENS, "w", encoding="utf-8") as f:
        json.dump({"personagens": personagens}, f, ensure_ascii=False, indent=2)


# =============================================================================
# BESTIARIO
# =============================================================================


def carregar_bestiario():
    if _modo() == "remoto":
        return _http_get("/bestiario")
    if not os.path.exists(ARQUIVO_BESTIARIO):
        return []
    try:
        with open(ARQUIVO_BESTIARIO, "r", encoding="utf-8") as f:
            return json.load(f).get("monstros", [])
    except (json.JSONDecodeError, OSError):
        return []


def salvar_bestiario(monstros):
    if _modo() == "remoto":
        _http_put("/bestiario", json_body=monstros)
        return
    with open(ARQUIVO_BESTIARIO, "w", encoding="utf-8") as f:
        json.dump({"monstros": monstros}, f, ensure_ascii=False, indent=2)


# =============================================================================
# IMAGENS
# =============================================================================


def copiar_imagem(origem):
    """Aceita um path local (escolhido pelo filedialog) e devolve o id da
    imagem — path relativo em modo local, nome UUID em modo remoto."""
    if _modo() == "remoto":
        return _upload_imagem_remoto(origem)
    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    extensao = os.path.splitext(origem)[1].lower() or ".png"
    nome = f"{uuid.uuid4().hex}{extensao}"
    destino = os.path.join(PASTA_IMAGENS, nome)
    shutil.copy2(origem, destino)
    return os.path.relpath(destino, PASTA_BASE).replace("\\", "/")


def caminho_imagem(id_imagem):
    """Resolve o id para um path absoluto no disco local. Em modo remoto
    baixa e cacheia em imagens_cache/ no primeiro acesso."""
    if not id_imagem:
        return None
    if _modo() == "remoto":
        nome = os.path.basename(id_imagem)
        os.makedirs(PASTA_IMAGENS_CACHE, exist_ok=True)
        destino = os.path.join(PASTA_IMAGENS_CACHE, nome)
        if not os.path.exists(destino):
            try:
                _baixar_imagem_remota(nome, destino)
            except Exception:
                return None
        return destino
    if os.path.isabs(id_imagem):
        return id_imagem
    return os.path.join(PASTA_BASE, id_imagem)


# =============================================================================
# HTTP (modo remoto)
# =============================================================================


TIMEOUT_SEGUNDOS = 15


def _exigir_requests():
    if requests is None:
        raise ErroServidor(
            "modo remoto requer a biblioteca `requests`. rode: pip install requests"
        )


def _url(path):
    base = _servidor_url()
    if not base:
        raise ErroServidor("servidor_url nao configurada em app.json")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _headers_auth():
    token = _token()
    if not token:
        raise ErroAutenticacao("nao autenticado (token ausente)", campo=None)
    return {"X-Auth-Token": token}


def _tratar_resposta(resp):
    if resp.status_code == 401:
        raise ErroAutenticacao(
            "sessao expirada — faca login novamente", campo=None
        )
    if resp.status_code == 403:
        raise ErroPermissao("sem permissao para essa operacao")
    if resp.status_code >= 400:
        try:
            detalhe = resp.json().get("erro") or resp.text
        except ValueError:
            detalhe = resp.text
        raise ErroServidor(
            f"servidor retornou {resp.status_code}: {detalhe}"
        )
    return resp


def _login_remoto(usuario, senha, palavra_chave):
    _exigir_requests()
    try:
        resp = requests.post(
            _url("/login"),
            json={
                "usuario": usuario,
                "senha": senha,
                "palavra_chave": palavra_chave,
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as erro:
        raise ErroServidor(f"falha ao conectar: {erro}") from erro

    if resp.status_code == 401:
        try:
            motivo = resp.json().get("erro", "credenciais invalidas")
        except ValueError:
            motivo = "credenciais invalidas"
        campo = None
        m = motivo.lower()
        if "usuario" in m:
            campo = "usuario"
        elif "senha" in m:
            campo = "senha"
        elif "palavra" in m:
            campo = "palavra_chave"
        raise ErroAutenticacao(motivo, campo=campo)

    _tratar_resposta(resp)
    dados = resp.json()
    token = dados.get("token")
    canonico = dados.get("usuario", usuario)
    papel = dados.get("papel", "jogador")

    cfg = carregar_app_config()
    cfg["token"] = token
    cfg["usuario"] = canonico
    salvar_app_config(cfg)

    return canonico, papel


def _http_get(path):
    _exigir_requests()
    try:
        resp = requests.get(
            _url(path), headers=_headers_auth(), timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as erro:
        raise ErroServidor(f"falha ao conectar: {erro}") from erro
    _tratar_resposta(resp)
    if not resp.content:
        return None
    return resp.json()


def _http_post(path, json_body=None):
    _exigir_requests()
    try:
        resp = requests.post(
            _url(path), headers=_headers_auth(),
            json=json_body, timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as erro:
        raise ErroServidor(f"falha ao conectar: {erro}") from erro
    _tratar_resposta(resp)
    if not resp.content:
        return None
    return resp.json()


def _http_put(path, json_body=None):
    _exigir_requests()
    try:
        resp = requests.put(
            _url(path), headers=_headers_auth(),
            json=json_body, timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as erro:
        raise ErroServidor(f"falha ao conectar: {erro}") from erro
    _tratar_resposta(resp)
    return resp.status_code


def _http_delete(path):
    _exigir_requests()
    try:
        resp = requests.delete(
            _url(path), headers=_headers_auth(), timeout=TIMEOUT_SEGUNDOS,
        )
    except requests.RequestException as erro:
        raise ErroServidor(f"falha ao conectar: {erro}") from erro
    _tratar_resposta(resp)
    return resp.status_code


def _upload_imagem_remoto(origem):
    _exigir_requests()
    try:
        with open(origem, "rb") as f:
            resp = requests.post(
                _url("/imagens"),
                headers=_headers_auth(),
                files={"file": (os.path.basename(origem), f)},
                timeout=TIMEOUT_SEGUNDOS * 2,
            )
    except requests.RequestException as erro:
        raise ErroServidor(f"falha ao enviar imagem: {erro}") from erro
    _tratar_resposta(resp)
    nome = resp.json().get("nome")
    if not nome:
        raise ErroServidor("servidor nao devolveu nome da imagem")
    # pre-popula o cache local pra proxima leitura ser instantanea
    os.makedirs(PASTA_IMAGENS_CACHE, exist_ok=True)
    destino = os.path.join(PASTA_IMAGENS_CACHE, nome)
    try:
        shutil.copy2(origem, destino)
    except OSError:
        pass
    return nome


def _baixar_imagem_remota(nome, destino):
    _exigir_requests()
    try:
        resp = requests.get(
            _url(f"/imagens/{nome}"), headers=_headers_auth(),
            timeout=TIMEOUT_SEGUNDOS, stream=True,
        )
    except requests.RequestException as erro:
        raise ErroServidor(f"falha ao baixar imagem: {erro}") from erro
    _tratar_resposta(resp)
    with open(destino, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
