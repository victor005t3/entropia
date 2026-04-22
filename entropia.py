"""
ENTROPIA - Sistema de RPG
Aplicativo desktop para mesa de RPG proprio.

Para rodar: python entropia.py
Requer: Python 3.8+ (Tkinter ja vem incluido) e Pillow (pip install pillow).
"""

import random
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

# =============================================================================
# CADASTRO DE USUARIOS
# -----------------------------------------------------------------------------
# Para adicionar um novo login, basta incluir uma nova entrada no dicionario
# abaixo. A estrutura e:
#     "nome_de_usuario": {
#         "senha": "senha_do_usuario",
#         "palavra_chave": "palavra_chave_secreta",
#         "papel": "mestre"  ou  "jogador"
#     }
# =============================================================================

USUARIOS = {
    "O MESTRE": {
        "senha": "thebes.1995",
        "palavra_chave": "entropia",
        "papel": "mestre",
    },
    "AMÍLIA": {
        "senha": "euamoneptuno06",
        "palavra_chave": "gato frajola",
        "papel": "jogador",
    },
    "DANTE": {
        "senha": "meu_taco",
        "palavra_chave": "diálogo",
        "papel": "jogador",
    },
    "WYATT": {
        "senha": "courier",
        "palavra_chave": "240698",
        "papel": "jogador",
    },
    "GUIZO": {
        "senha": "692012",
        "palavra_chave": "combatente",
        "papel": "Jogador",
    }
}

# =============================================================================
# CORES E ESTILO
# =============================================================================

COR_FUNDO = "#000000"
COR_FUNDO_PAINEL = "#0a0a0a"
COR_FUNDO_CAMPO = "#111111"
COR_BORDA = "#2a2a2a"
COR_TEXTO = "#e8e8e8"
COR_TEXTO_SUAVE = "#888888"
COR_TEXTO_FRACO = "#555555"
COR_DESTAQUE = "#44008c"
COR_DESTAQUE_HOVER = "#500086"
COR_VIDA = "#8b0000"
COR_VIDA_FUNDO = "#1a0303"
COR_ENERGIA = "#1e5fbf"
COR_ENERGIA_FUNDO = "#061022"
COR_SANIDADE = "#6b2aa8"
COR_SANIDADE_FUNDO = "#140520"

FONTE_TITULO = ("Segoe UI Light", 30)
FONTE_SUBTITULO = ("Segoe UI Light", 10)
FONTE_LABEL = ("Segoe UI", 8)
FONTE_CAMPO = ("Segoe UI", 11)
FONTE_BOTAO = ("Segoe UI", 10)
FONTE_DISCRETA = ("Segoe UI", 9)
FONTE_SECAO = ("Segoe UI Light", 18)

# =============================================================================
# REGRAS DE JOGO
# -----------------------------------------------------------------------------
# VIDA: 15 no LC 0, +15 por LC. VITALIDADE soma +5 por ponto.
# ENERGIA: 18 no LC 0, +12 por LC. PRESENCA soma +4 por ponto.
# SANIDADE: 0 a 150, comeca em 100.
# =============================================================================

VIDA_BASE = 15
VIDA_POR_LC = 15
ENERGIA_BASE = 18
ENERGIA_POR_LC = 12
BONUS_VITALIDADE = 5
BONUS_PRESENCA = 4
SANIDADE_MAX = 150
SANIDADE_INICIAL = 100

ATRIBUTOS_NOMES = [
    "AGILIDADE",
    "CRISTAL",
    "FORCA",
    "INTELIGENCIA",
    "PRESENCA",
    "VITALIDADE",
]

# =============================================================================
# MAESTRIAS
# -----------------------------------------------------------------------------
# Dois grupos fechados; cada nivel vai de 0 a MAESTRIA_MAX.
# =============================================================================

MAESTRIAS_ELEMENTAIS = ("AGUA", "TERRA", "FOGO", "AR")
MAESTRIAS_PRIMORDIAIS = ("ABISMO", "LUMEN", "ETER", "NUCLEO", "NOUS")
MAESTRIA_MAX = 6

# =============================================================================
# ARMAMENTOS
# -----------------------------------------------------------------------------
# Categorias pre-definidas. Apenas Pistola e Rifle usam municao (atual/maxima).
# Dano em notacao de dados: NdM[+K]  (ex: 1d6, 2d6+3).
# =============================================================================

TIPOS_ARMA = ["Pistola", "Rifle", "Faca", "Grimorio", "Outro"]
TIPOS_COM_MUNICAO = {"Pistola", "Rifle"}
TIPO_ARMA_PADRAO = "Pistola"
DICA_DANO = "ex: 1d6, 2d6+3 (N dados de M lados)"

TIPOS_ITEM = ["Municao", "Cura", "Consumivel", "Equipamento", "Outro"]
TIPO_ITEM_PADRAO = "Outro"


def calcular_vida_maxima(nivel_lc, vitalidade):
    nivel = 0 if nivel_lc is None else nivel_lc
    return VIDA_BASE + nivel * VIDA_POR_LC + vitalidade * BONUS_VITALIDADE


def calcular_energia_maxima(nivel_lc, presenca):
    nivel = 0 if nivel_lc is None else nivel_lc
    return ENERGIA_BASE + nivel * ENERGIA_POR_LC + presenca * BONUS_PRESENCA

# =============================================================================
# PERSISTENCIA
# -----------------------------------------------------------------------------
# Funcoes de I/O vivem em persistencia.py, que dispacha local/remoto com
# base em app.json. A API abaixo e exportada dali e usada como antes:
#     carregar_personagens, salvar_personagem, atualizar_personagem,
#     remover_personagem, carregar_bestiario, salvar_bestiario,
#     copiar_imagem, caminho_imagem, login
# =============================================================================

from persistencia import (
    ErroAutenticacao,
    atualizar_personagem,
    caminho_imagem,
    carregar_bestiario,
    carregar_habilidades,
    carregar_personagens,
    copiar_imagem,
    login as autenticar,
    remover_personagem,
    salvar_bestiario,
    salvar_habilidade,
    salvar_personagem,
)


# =============================================================================
# TELA DE LOGIN
# =============================================================================


class TelaLogin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ENTROPIA")
        self.configure(bg=COR_FUNDO)
        self.geometry("480x560")
        self.resizable(False, False)

        self.attributes("-alpha", 0.0)

        self._centralizar()
        self._montar_interface()

        self.after(80, self._fade_in)

    def _fade_in(self, alpha=0.0, passo=0.04, intervalo=16):
        alpha = min(1.0, alpha + passo)
        self.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.after(intervalo, lambda: self._fade_in(alpha, passo, intervalo))

    def _centralizar(self):
        self.update_idletasks()
        largura = 480
        altura = 560
        x = (self.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.winfo_screenheight() // 2) - (altura // 2)
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def _montar_interface(self):
        container = tk.Frame(self, bg=COR_FUNDO)
        container.pack(expand=True, fill="both", padx=50, pady=40)

        tk.Label(
            container,
            text="ENTROPIA",
            font=FONTE_TITULO,
            bg=COR_FUNDO,
            fg=COR_TEXTO,
        ).pack(pady=(20, 4))

        tk.Label(
            container,
            text="O Caos Sempre Reina.",
            font=FONTE_SUBTITULO,
            bg=COR_FUNDO,
            fg=COR_TEXTO_SUAVE,
        ).pack(pady=(0, 30))

        self.campo_usuario = self._criar_campo(container, "Usuario")
        self.campo_senha = self._criar_campo(container, "Senha", ocultar=True)
        self.campo_palavra = self._criar_campo(container, "Palavra-chave", ocultar=True)

        botao = tk.Label(
            container,
            text="ENTRAR",
            font=FONTE_BOTAO,
            bg=COR_DESTAQUE,
            fg=COR_TEXTO,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        botao.pack(fill="x", pady=(18, 0))
        botao.bind("<Button-1>", lambda e: self._tentar_login())
        botao.bind("<Enter>", lambda e: botao.configure(bg=COR_DESTAQUE_HOVER))
        botao.bind("<Leave>", lambda e: botao.configure(bg=COR_DESTAQUE))

        self.mensagem = tk.Label(
            container,
            text="",
            font=FONTE_LABEL,
            bg=COR_FUNDO,
            fg=COR_DESTAQUE_HOVER,
        )
        self.mensagem.pack(pady=(14, 0))

        self.bind("<Return>", lambda e: self._tentar_login())
        self.campo_usuario.focus_set()

    def _criar_campo(self, parent, rotulo, ocultar=False):
        tk.Label(
            parent,
            text=rotulo.lower(),
            font=FONTE_LABEL,
            bg=COR_FUNDO,
            fg=COR_TEXTO_SUAVE,
            anchor="w",
        ).pack(fill="x", pady=(14, 2))

        entrada = tk.Entry(
            parent,
            font=FONTE_CAMPO,
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            insertbackground=COR_TEXTO,
            relief="flat",
            bd=0,
            show="*" if ocultar else "",
        )
        entrada.pack(fill="x", pady=(0, 2))

        linha = tk.Frame(parent, bg=COR_BORDA, height=1)
        linha.pack(fill="x")

        entrada.bind("<FocusIn>", lambda e: linha.configure(bg=COR_DESTAQUE))
        entrada.bind("<FocusOut>", lambda e: linha.configure(bg=COR_BORDA))

        return entrada

    def _tentar_login(self):
        usuario = " ".join(self.campo_usuario.get().split())
        senha = self.campo_senha.get()
        palavra = self.campo_palavra.get().strip()

        if not usuario or not senha or not palavra:
            self._mostrar_erro("Preencha todos os campos.")
            return

        try:
            usuario_canonico, papel = autenticar(usuario, senha, palavra)
        except ErroAutenticacao as erro:
            self._mostrar_erro(erro.motivo)
            return
        except Exception as erro:
            self._mostrar_erro(f"Falha ao conectar: {erro}")
            return

        self.destroy()
        TelaPrincipal(usuario=usuario_canonico, papel=papel).mainloop()

    def _mostrar_erro(self, texto):
        self.mensagem.configure(text=texto)
        self.after(3000, lambda: self.mensagem.configure(text=""))


# =============================================================================
# TELA PRINCIPAL (pos-login, em janela maximizada)
# =============================================================================


class TelaPrincipal(tk.Tk):
    def __init__(self, usuario, papel):
        super().__init__()
        self.usuario = usuario
        self.papel = papel

        self.aba_atual = "personagens"
        self.tab_labels = {}
        self.frames_aba = {}
        self.historico_rolagens = []
        self.bestiario = carregar_bestiario() if self._eh_mestre() else []
        self._bestiario_imagens = []

        self.title(f"ENTROPIA - {usuario}")
        self.configure(bg=COR_FUNDO)
        self.geometry("1200x720")
        try:
            self.state("zoomed")
        except tk.TclError:
            self.attributes("-zoomed", True)

        self._montar_interface()

    def _montar_interface(self):
        topo = tk.Frame(self, bg=COR_FUNDO_PAINEL, height=56)
        topo.pack(fill="x")
        topo.pack_propagate(False)

        tk.Label(
            topo,
            text="ENTROPIA",
            font=("Segoe UI Light", 16),
            bg=COR_FUNDO_PAINEL,
            fg=COR_TEXTO,
            padx=24,
        ).pack(side="left")

        tk.Label(
            topo,
            text=f"{self.usuario}  ·  {self.papel.upper()}",
            font=FONTE_DISCRETA,
            bg=COR_FUNDO_PAINEL,
            fg=COR_TEXTO_SUAVE,
            padx=24,
        ).pack(side="right")

        self._montar_abas_principal(topo)

        self.area = tk.Frame(self, bg=COR_FUNDO)
        self.area.pack(expand=True, fill="both", padx=40, pady=(24, 40))

        self.frames_aba["personagens"] = tk.Frame(self.area, bg=COR_FUNDO)
        self.frames_aba["rolador"] = tk.Frame(self.area, bg=COR_FUNDO)

        self._montar_aba_personagens(self.frames_aba["personagens"])
        self._montar_aba_rolador(self.frames_aba["rolador"])

        if self._eh_mestre():
            self.frames_aba["bestiario"] = tk.Frame(self.area, bg=COR_FUNDO)
            self._montar_aba_bestiario(self.frames_aba["bestiario"])

        self._trocar_aba_principal("personagens")

    def _montar_abas_principal(self, topo):
        barra = tk.Frame(topo, bg=COR_FUNDO_PAINEL)
        barra.pack(side="left", padx=(40, 0))

        abas = [("personagens", "Personagens"), ("rolador", "Rolador")]
        if self._eh_mestre():
            abas.append(("bestiario", "Bestiario"))

        for chave, rotulo in abas:
            label = tk.Label(
                barra, text=rotulo, font=FONTE_BOTAO,
                bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
                padx=14, pady=5, cursor="hand2",
            )
            label.pack(side="left", padx=(0, 4))
            label.bind("<Button-1>", lambda e, c=chave: self._trocar_aba_principal(c))
            self.tab_labels[chave] = label

    def _trocar_aba_principal(self, chave):
        self.aba_atual = chave
        for nome, label in self.tab_labels.items():
            if nome == chave:
                label.configure(bg=COR_DESTAQUE, fg=COR_TEXTO)
            else:
                label.configure(bg=COR_FUNDO_CAMPO, fg=COR_TEXTO)
        for nome, frame in self.frames_aba.items():
            if nome == chave:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    def _montar_aba_personagens(self, parent):
        cabecalho = tk.Frame(parent, bg=COR_FUNDO)
        cabecalho.pack(fill="x", pady=(0, 16))

        self.label_contagem = tk.Label(
            cabecalho,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO,
            fg=COR_TEXTO,
        )
        self.label_contagem.pack(side="left")

        botao_novo = tk.Label(
            cabecalho,
            text="Novo Personagem",
            font=FONTE_BOTAO,
            bg=COR_DESTAQUE,
            fg=COR_TEXTO,
            padx=16,
            pady=6,
            cursor="hand2",
        )
        botao_novo.pack(side="right")
        botao_novo.bind("<Button-1>", lambda e: self._abrir_criacao())
        botao_novo.bind("<Enter>", lambda e: botao_novo.configure(bg=COR_DESTAQUE_HOVER))
        botao_novo.bind("<Leave>", lambda e: botao_novo.configure(bg=COR_DESTAQUE))

        self.grade = tk.Frame(parent, bg=COR_FUNDO)
        self.grade.pack(fill="both", expand=True)

        self._card_imagens = []
        self._renderizar_lista()

    def _eh_mestre(self):
        return str(self.papel).casefold() == "mestre"

    def _renderizar_lista(self):
        for child in self.grade.winfo_children():
            child.destroy()
        self._card_imagens.clear()

        todos = carregar_personagens()
        if self._eh_mestre():
            meus = list(todos)
            self.label_contagem.configure(
                text=f"Personagens (visao do Mestre): {len(meus)}"
            )
        else:
            alvo = self.usuario.casefold()
            meus = [p for p in todos if str(p.get("criado_por", "")).casefold() == alvo]
            self.label_contagem.configure(text=f"Personagens: {len(meus)}")

        if not meus:
            tk.Label(
                self.grade,
                text="Nenhum personagem ainda. Clique em 'Novo Personagem' para comecar.",
                font=FONTE_DISCRETA,
                bg=COR_FUNDO,
                fg=COR_TEXTO_FRACO,
            ).pack(pady=40)
            return

        colunas = 3
        for i in range(colunas):
            self.grade.grid_columnconfigure(i, weight=1, uniform="col")

        for idx, personagem in enumerate(meus):
            linha = idx // colunas
            coluna = idx % colunas
            card = self._criar_card(self.grade, personagem)
            card.grid(row=linha, column=coluna, padx=8, pady=8, sticky="nsew")

    def _criar_card(self, parent, personagem):
        card = tk.Frame(
            parent,
            bg=COR_FUNDO_PAINEL,
            highlightthickness=1,
            highlightbackground=COR_BORDA,
        )

        inner = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        topo = tk.Frame(inner, bg=COR_FUNDO_PAINEL)
        topo.pack(fill="x")

        img_path = personagem.get("imagem") or ""
        if img_path:
            caminho_abs = caminho_imagem(img_path)
            try:
                img = Image.open(caminho_abs)
                img.thumbnail((70, 70), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self._card_imagens.append(tk_img)
                tk.Label(
                    topo, image=tk_img, bg=COR_FUNDO_PAINEL,
                ).pack(side="left", padx=(0, 10), anchor="n")
            except Exception:
                pass

        meio = tk.Frame(topo, bg=COR_FUNDO_PAINEL)
        meio.pack(side="left", fill="x", expand=True, anchor="n")

        linha_nome = tk.Frame(meio, bg=COR_FUNDO_PAINEL)
        linha_nome.pack(fill="x")

        nome = personagem.get("nome") or "[Sem nome]"
        tk.Label(
            linha_nome,
            text=nome,
            font=("Segoe UI", 13),
            bg=COR_FUNDO_PAINEL,
            fg=COR_TEXTO,
            anchor="w",
        ).pack(side="left")

        is_dono = str(personagem.get("criado_por", "")).casefold() == self.usuario.casefold()
        pode_administrar = is_dono or self._eh_mestre()

        if pode_administrar:
            excluir = tk.Label(
                linha_nome,
                text="\u2715",
                font=("Segoe UI", 11),
                bg=COR_FUNDO_PAINEL,
                fg=COR_TEXTO_SUAVE,
                cursor="hand2",
            )
            excluir.pack(side="right")
            excluir.bind("<Button-1>", lambda e, p=personagem: self._excluir_personagem(p))
            excluir.bind("<Enter>", lambda e, w=excluir: w.configure(fg=COR_VIDA))
            excluir.bind("<Leave>", lambda e, w=excluir: w.configure(fg=COR_TEXTO_SUAVE))

        nivel = personagem.get("nivel_lc")
        nivel_txt = f"LC {nivel}" if nivel is not None else "Sem LC"
        tk.Label(
            meio,
            text=nivel_txt,
            font=("Segoe UI", 9),
            bg=COR_FUNDO_PAINEL,
            fg=COR_TEXTO_SUAVE,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        if self._eh_mestre() and not is_dono:
            dono = personagem.get("criado_por", "?")
            tk.Label(
                meio,
                text=f"jogador: {dono}",
                font=("Segoe UI", 8),
                bg=COR_FUNDO_PAINEL,
                fg=COR_DESTAQUE_HOVER,
                anchor="w",
            ).pack(fill="x", pady=(2, 0))

        data = personagem.get("criado_em", "")
        if data:
            tk.Label(
                meio,
                text=f"Registrado em {data}",
                font=("Segoe UI", 8),
                bg=COR_FUNDO_PAINEL,
                fg=COR_DESTAQUE_HOVER,
                anchor="w",
            ).pack(fill="x", pady=(6, 0))

        rodape = tk.Frame(inner, bg=COR_FUNDO_PAINEL)
        rodape.pack(fill="x", pady=(10, 0))

        acessar = tk.Label(
            rodape,
            text="Acessar Ficha",
            font=("Segoe UI", 9),
            bg=COR_DESTAQUE,
            fg=COR_TEXTO,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        acessar.pack(side="right")
        acessar.bind("<Button-1>", lambda e, p=personagem: self._abrir_ficha(p))
        acessar.bind("<Enter>", lambda e: acessar.configure(bg=COR_DESTAQUE_HOVER))
        acessar.bind("<Leave>", lambda e: acessar.configure(bg=COR_DESTAQUE))

        return card

    def _abrir_ficha(self, personagem):
        is_dono = str(personagem.get("criado_por", "")).casefold() == self.usuario.casefold()
        if is_dono or self._eh_mestre():
            dialog = TelaCriacaoPersonagem(
                self,
                criado_por=personagem.get("criado_por", self.usuario),
                personagem_existente=personagem,
            )
            self.wait_window(dialog)
            self._renderizar_lista()
        else:
            messagebox.showinfo(
                "Em breve",
                f"Ficha de '{personagem.get('nome', 'personagem')}' em modo leitura "
                f"sera implementada na proxima etapa do roadmap.",
                parent=self,
            )

    def _excluir_personagem(self, personagem):
        nome = personagem.get("nome", "personagem")
        resposta = messagebox.askyesno(
            "Excluir personagem",
            f"Tem certeza que quer excluir '{nome}'? Esta acao nao pode ser desfeita.",
            parent=self,
        )
        if not resposta:
            return
        if remover_personagem(personagem.get("id")):
            self._renderizar_lista()
        else:
            messagebox.showerror("Erro", "Nao foi possivel excluir o personagem.", parent=self)

    def _abrir_criacao(self):
        dialog = TelaCriacaoPersonagem(self, criado_por=self.usuario)
        self.wait_window(dialog)
        self._renderizar_lista()

    # ----- aba rolador de dados -----

    def _montar_aba_rolador(self, parent):
        tk.Label(
            parent, text="ROLADOR DE DADOS",
            font=("Segoe UI Light", 16),
            bg=COR_FUNDO, fg=COR_TEXTO, anchor="w",
        ).pack(fill="x", pady=(0, 12))

        config = tk.Frame(parent, bg=COR_FUNDO)
        config.pack(fill="x", pady=(0, 14))

        tk.Label(
            config, text="qtd", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE,
        ).pack(side="left", padx=(0, 4))

        self.entry_qtd_dados = tk.Entry(
            config, font=FONTE_CAMPO, width=5, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        self.entry_qtd_dados.insert(0, "1")
        self.entry_qtd_dados.pack(side="left", padx=(0, 8))

        tk.Label(
            config, text="d", font=("Segoe UI", 14),
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE,
        ).pack(side="left", padx=(0, 4))

        self.entry_lados_dados = tk.Entry(
            config, font=FONTE_CAMPO, width=5, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        self.entry_lados_dados.insert(0, "6")
        self.entry_lados_dados.pack(side="left", padx=(0, 16))

        tk.Label(
            config, text="modificador", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE,
        ).pack(side="left", padx=(0, 4))

        self.entry_modificador = tk.Entry(
            config, font=FONTE_CAMPO, width=5, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        self.entry_modificador.insert(0, "0")
        self.entry_modificador.pack(side="left", padx=(0, 16))

        botao_rolar = tk.Label(
            config, text="Rolar", font=FONTE_BOTAO,
            bg=COR_DESTAQUE, fg=COR_TEXTO,
            padx=18, pady=6, cursor="hand2",
        )
        botao_rolar.pack(side="left")
        botao_rolar.bind("<Button-1>", lambda e: self._rolar_dados())
        botao_rolar.bind("<Enter>", lambda e: botao_rolar.configure(bg=COR_DESTAQUE_HOVER))
        botao_rolar.bind("<Leave>", lambda e: botao_rolar.configure(bg=COR_DESTAQUE))

        self.label_erro_rolagem = tk.Label(
            config, text="", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_DESTAQUE_HOVER,
        )
        self.label_erro_rolagem.pack(side="left", padx=(14, 0))

        self.bind("<Return>", lambda e: self._rolar_dados())

        # ultima rolagem em destaque
        painel = tk.Frame(parent, bg=COR_FUNDO_PAINEL,
                          highlightthickness=1, highlightbackground=COR_BORDA)
        painel.pack(fill="x", pady=(0, 16))

        tk.Label(
            painel, text="ultima rolagem", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(anchor="w", padx=14, pady=(10, 0))

        self.label_ultima_rolagem = tk.Label(
            painel,
            text="(nenhuma rolagem ainda)",
            font=("Segoe UI Light", 22),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO,
            anchor="w", justify="left",
        )
        self.label_ultima_rolagem.pack(fill="x", padx=14, pady=(2, 4))

        self.label_detalhe_rolagem = tk.Label(
            painel, text="", font=FONTE_DISCRETA,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE,
            anchor="w", justify="left",
        )
        self.label_detalhe_rolagem.pack(fill="x", padx=14, pady=(0, 12))

        # historico
        cab_hist = tk.Frame(parent, bg=COR_FUNDO)
        cab_hist.pack(fill="x", pady=(0, 4))

        tk.Label(
            cab_hist, text="HISTORICO (sessao atual)",
            font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO,
        ).pack(side="left")

        botao_limpar = tk.Label(
            cab_hist, text="Limpar", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE,
            padx=10, pady=4, cursor="hand2",
        )
        botao_limpar.pack(side="right")
        botao_limpar.bind("<Button-1>", lambda e: self._limpar_historico_rolagens())
        botao_limpar.bind("<Enter>", lambda e: botao_limpar.configure(fg=COR_VIDA))
        botao_limpar.bind("<Leave>", lambda e: botao_limpar.configure(fg=COR_TEXTO_SUAVE))

        moldura = tk.Frame(parent, bg=COR_FUNDO,
                           highlightthickness=1, highlightbackground=COR_BORDA)
        moldura.pack(fill="both", expand=True)

        self.lista_historico = tk.Listbox(
            moldura, bg=COR_FUNDO_PAINEL, fg=COR_TEXTO,
            selectbackground=COR_DESTAQUE, selectforeground=COR_TEXTO,
            font=("Consolas", 10), bd=0, highlightthickness=0,
            activestyle="none",
        )
        scrollbar_hist = tk.Scrollbar(moldura, orient="vertical",
                                      command=self.lista_historico.yview)
        self.lista_historico.configure(yscrollcommand=scrollbar_hist.set)
        scrollbar_hist.pack(side="right", fill="y")
        self.lista_historico.pack(side="left", fill="both", expand=True)

        self._renderizar_historico_rolagens()

    def _rolar_dados(self):
        if self.aba_atual != "rolador":
            return
        try:
            qtd = int(self.entry_qtd_dados.get())
            lados = int(self.entry_lados_dados.get())
            mod_txt = self.entry_modificador.get().strip() or "0"
            mod = int(mod_txt)
        except ValueError:
            self._mostrar_erro_rolagem("digite numeros validos")
            return

        if qtd < 1 or qtd > 100:
            self._mostrar_erro_rolagem("qtd deve estar entre 1 e 100")
            return
        if lados < 2:
            self._mostrar_erro_rolagem("o dado precisa ter ao menos 2 lados")
            return

        rolagens = [random.randint(1, lados) for _ in range(qtd)]
        soma = sum(rolagens)
        total = soma + mod
        sufixo_mod = f"{mod:+d}" if mod else ""
        expressao = f"{qtd}d{lados}{sufixo_mod}"

        entrada = {
            "expressao": expressao,
            "rolagens": rolagens,
            "modificador": mod,
            "total": total,
        }
        self.historico_rolagens.insert(0, entrada)
        self.historico_rolagens = self.historico_rolagens[:50]

        self.label_ultima_rolagem.configure(text=f"{expressao}  =  {total}")
        detalhes = f"rolagens: {rolagens}  |  soma: {soma}"
        if mod:
            detalhes += f"  |  modificador: {mod:+d}"
        self.label_detalhe_rolagem.configure(text=detalhes)

        self._renderizar_historico_rolagens()

    def _mostrar_erro_rolagem(self, texto):
        self.label_erro_rolagem.configure(text=texto)
        self.after(3000, lambda: self.label_erro_rolagem.configure(text=""))

    def _renderizar_historico_rolagens(self):
        self.lista_historico.delete(0, tk.END)
        if not self.historico_rolagens:
            self.lista_historico.insert(tk.END, "  (nenhuma rolagem nesta sessao)")
            self.lista_historico.itemconfigure(0, fg=COR_TEXTO_FRACO)
            return
        for entrada in self.historico_rolagens:
            linha = f"  {entrada['expressao']:<14}  {str(entrada['rolagens']):<28}  =  {entrada['total']}"
            self.lista_historico.insert(tk.END, linha)

    def _limpar_historico_rolagens(self):
        self.historico_rolagens.clear()
        self._renderizar_historico_rolagens()

    # ----- aba bestiario (somente mestre) -----

    def _montar_aba_bestiario(self, parent):
        cabecalho = tk.Frame(parent, bg=COR_FUNDO)
        cabecalho.pack(fill="x", pady=(0, 10))

        adicionar = tk.Label(
            cabecalho, text="+ Adicionar monstro", font=FONTE_BOTAO,
            bg=COR_DESTAQUE, fg=COR_TEXTO,
            padx=14, pady=6, cursor="hand2",
        )
        adicionar.pack(side="left")
        adicionar.bind("<Button-1>", lambda e: self._adicionar_monstro())
        adicionar.bind("<Enter>", lambda e: adicionar.configure(bg=COR_DESTAQUE_HOVER))
        adicionar.bind("<Leave>", lambda e: adicionar.configure(bg=COR_DESTAQUE))

        self.label_vazio_bestiario = tk.Label(
            cabecalho, text="nenhum monstro cadastrado", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        )
        self.label_vazio_bestiario.pack(side="left", padx=(14, 0))

        moldura = tk.Frame(parent, bg=COR_FUNDO,
                           highlightthickness=1, highlightbackground=COR_BORDA)
        moldura.pack(fill="both", expand=True)

        self.canvas_bestiario = tk.Canvas(
            moldura, bg=COR_FUNDO, highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(moldura, orient="vertical",
                                 command=self.canvas_bestiario.yview)
        self.canvas_bestiario.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas_bestiario.pack(side="left", fill="both", expand=True)

        self.frame_bestiario = tk.Frame(self.canvas_bestiario, bg=COR_FUNDO)
        janela = self.canvas_bestiario.create_window(
            (0, 0), window=self.frame_bestiario, anchor="nw",
        )

        self.canvas_bestiario.bind(
            "<Configure>",
            lambda e: self.canvas_bestiario.itemconfigure(janela, width=e.width),
        )
        self.frame_bestiario.bind(
            "<Configure>",
            lambda e: self.canvas_bestiario.configure(scrollregion=self.canvas_bestiario.bbox("all")),
        )
        self.canvas_bestiario.bind(
            "<Enter>",
            lambda e: self.canvas_bestiario.bind_all(
                "<MouseWheel>",
                lambda ev: self.canvas_bestiario.yview_scroll(int(-1 * (ev.delta / 120)), "units"),
            ),
        )
        self.canvas_bestiario.bind(
            "<Leave>",
            lambda e: self.canvas_bestiario.unbind_all("<MouseWheel>"),
        )

        self._renderizar_bestiario()

    def _renderizar_bestiario(self):
        for child in self.frame_bestiario.winfo_children():
            child.destroy()
        self._bestiario_imagens.clear()

        if not self.bestiario:
            self.label_vazio_bestiario.pack(side="left", padx=(14, 0))
        else:
            self.label_vazio_bestiario.pack_forget()

        for monstro in self.bestiario:
            self._criar_card_monstro(self.frame_bestiario, monstro).pack(
                fill="x", padx=8, pady=6,
            )

    TAMANHO_IMG_MONSTRO = 90

    def _criar_card_monstro(self, parent, monstro):
        card = tk.Frame(parent, bg=COR_FUNDO_PAINEL,
                        highlightthickness=1, highlightbackground=COR_BORDA)

        # coluna esquerda: imagem clicavel
        coluna_img = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        coluna_img.pack(side="left", padx=10, pady=10, anchor="n")

        quadro = tk.Frame(
            coluna_img, bg=COR_FUNDO_CAMPO,
            width=self.TAMANHO_IMG_MONSTRO, height=self.TAMANHO_IMG_MONSTRO,
            highlightthickness=1, highlightbackground=COR_BORDA,
        )
        quadro.pack()
        quadro.pack_propagate(False)

        label_img = tk.Label(
            quadro, text="clique para\nescolher", font=FONTE_LABEL,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO_SUAVE, cursor="hand2",
        )
        label_img.pack(expand=True, fill="both")

        self._carregar_imagem_monstro(label_img, monstro)

        label_img.bind(
            "<Button-1>",
            lambda e, m=monstro, lbl=label_img: self._escolher_imagem_monstro(m, lbl),
        )

        # coluna direita: campos
        conteudo = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        conteudo.pack(side="left", fill="both", expand=True)

        # linha 1: nome + excluir
        linha1 = tk.Frame(conteudo, bg=COR_FUNDO_PAINEL)
        linha1.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(
            linha1, text="nome", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        entry_nome = tk.Entry(
            linha1, font=FONTE_CAMPO,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_nome.insert(0, monstro.get("nome", ""))
        entry_nome.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def on_nome(_):
            monstro["nome"] = entry_nome.get()
            self._persistir_bestiario()

        entry_nome.bind("<KeyRelease>", on_nome)

        excluir = tk.Label(
            linha1, text="\u2715", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2",
        )
        excluir.pack(side="right")
        excluir.bind("<Button-1>", lambda e, mid=monstro["id"]: self._remover_monstro(mid))
        excluir.bind("<Enter>", lambda e: excluir.configure(fg=COR_VIDA))
        excluir.bind("<Leave>", lambda e: excluir.configure(fg=COR_TEXTO_SUAVE))

        # linha 2: VIDA
        self._montar_linha_recurso(
            conteudo, monstro, "vida_atual", "vida_maxima", "VIDA", COR_VIDA,
        )
        # linha 3: ENERGIA
        self._montar_linha_recurso(
            conteudo, monstro, "energia_atual", "energia_maxima", "ENERGIA", COR_ENERGIA,
        )

        # linha 4: descricao
        linha4 = tk.Frame(conteudo, bg=COR_FUNDO_PAINEL)
        linha4.pack(fill="x", padx=10, pady=(4, 10))

        tk.Label(
            linha4, text="descricao", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        entry_desc = tk.Entry(
            linha4, font=FONTE_LABEL,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_desc.insert(0, monstro.get("descricao", ""))
        entry_desc.pack(side="left", fill="x", expand=True)

        def on_desc(_):
            monstro["descricao"] = entry_desc.get()
            self._persistir_bestiario()

        entry_desc.bind("<KeyRelease>", on_desc)

        return card

    def _montar_linha_recurso(self, card, monstro, chave_atual, chave_maxima, rotulo, cor):
        linha = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha.pack(fill="x", padx=10, pady=(0, 4))

        tk.Label(
            linha, text=rotulo, font=("Segoe UI", 10, "bold"),
            bg=COR_FUNDO_PAINEL, fg=cor, width=8, anchor="w",
        ).pack(side="left")

        seta_esq = tk.Label(
            linha, text="\u25c0", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2", padx=4,
        )
        seta_esq.pack(side="left")

        entry_atual = tk.Entry(
            linha, font=FONTE_LABEL, width=5, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_atual.insert(0, str(int(monstro.get(chave_atual, 0) or 0)))
        entry_atual.pack(side="left", padx=2)

        tk.Label(
            linha, text="/", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left")

        entry_max = tk.Entry(
            linha, font=FONTE_LABEL, width=5, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_max.insert(0, str(int(monstro.get(chave_maxima, 0) or 0)))
        entry_max.pack(side="left", padx=2)

        seta_dir = tk.Label(
            linha, text="\u25b6", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2", padx=4,
        )
        seta_dir.pack(side="left")

        def sincronizar():
            try:
                atual = int(entry_atual.get())
            except ValueError:
                atual = int(monstro.get(chave_atual, 0) or 0)
            try:
                maxima = max(0, int(entry_max.get()))
            except ValueError:
                maxima = int(monstro.get(chave_maxima, 0) or 0)
            atual = max(0, min(maxima, atual))
            monstro[chave_atual] = atual
            monstro[chave_maxima] = maxima
            entry_atual.delete(0, tk.END)
            entry_atual.insert(0, str(atual))
            entry_max.delete(0, tk.END)
            entry_max.insert(0, str(maxima))
            self._persistir_bestiario()

        def ajustar(delta):
            try:
                atual = int(entry_atual.get())
            except ValueError:
                atual = int(monstro.get(chave_atual, 0) or 0)
            entry_atual.delete(0, tk.END)
            entry_atual.insert(0, str(atual + delta))
            sincronizar()

        seta_esq.bind("<Button-1>", lambda e: ajustar(-1))
        seta_dir.bind("<Button-1>", lambda e: ajustar(1))
        for ent in (entry_atual, entry_max):
            ent.bind("<FocusOut>", lambda e: sincronizar())
            ent.bind("<Return>", lambda e: sincronizar())

    def _adicionar_monstro(self):
        self.bestiario.append({
            "id": uuid.uuid4().hex,
            "nome": "",
            "vida_atual": 10,
            "vida_maxima": 10,
            "energia_atual": 10,
            "energia_maxima": 10,
            "descricao": "",
            "imagem": "",
        })
        self._persistir_bestiario()
        self._renderizar_bestiario()

    def _remover_monstro(self, monstro_id):
        monstro = next((m for m in self.bestiario if m.get("id") == monstro_id), None)
        nome = (monstro or {}).get("nome") or "monstro"
        if not messagebox.askyesno(
            "Excluir monstro", f"Excluir '{nome}'?", parent=self,
        ):
            return
        self.bestiario = [m for m in self.bestiario if m.get("id") != monstro_id]
        self._persistir_bestiario()
        self._renderizar_bestiario()

    def _persistir_bestiario(self):
        try:
            salvar_bestiario(self.bestiario)
        except OSError as erro:
            messagebox.showerror(
                "Erro",
                f"Nao foi possivel salvar o bestiario:\n{erro}",
                parent=self,
            )

    def _carregar_imagem_monstro(self, label, monstro):
        imagem_path = monstro.get("imagem", "")
        if not imagem_path:
            return
        caminho_abs = caminho_imagem(imagem_path)
        if not caminho_abs:
            return
        try:
            img = Image.open(caminho_abs)
            img.thumbnail(
                (self.TAMANHO_IMG_MONSTRO, self.TAMANHO_IMG_MONSTRO),
                Image.LANCZOS,
            )
            tk_img = ImageTk.PhotoImage(img)
            self._bestiario_imagens.append(tk_img)
            label.configure(image=tk_img, text="")
        except Exception:
            pass

    def _escolher_imagem_monstro(self, monstro, label):
        caminho = filedialog.askopenfilename(
            parent=self,
            title="Escolher imagem do monstro",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return
        try:
            imagem_path = copiar_imagem(caminho)
        except Exception as erro:
            messagebox.showerror(
                "Erro",
                f"Nao foi possivel salvar a imagem:\n{erro}",
                parent=self,
            )
            return
        monstro["imagem"] = imagem_path
        self._persistir_bestiario()
        self._carregar_imagem_monstro(label, monstro)


# =============================================================================
# TELA DE CRIACAO DE PERSONAGEM
# =============================================================================


class DialogoCriarHabilidade(tk.Toplevel):
    LARGURA = 440
    ALTURA = 340

    def __init__(self, master):
        super().__init__(master)
        self.resultado = None

        self.title("Criar Habilidade")
        self.configure(bg=COR_FUNDO)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (self.LARGURA // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (self.ALTURA // 2)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{x}+{y}")

        self._montar()

    def _montar(self):
        container = tk.Frame(self, bg=COR_FUNDO)
        container.pack(expand=True, fill="both", padx=20, pady=14)

        tk.Label(
            container, text="Nova Habilidade", font=FONTE_SECAO,
            bg=COR_FUNDO, fg=COR_TEXTO, anchor="w",
        ).pack(fill="x", pady=(0, 10))

        tk.Label(
            container, text="nome", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE, anchor="w",
        ).pack(fill="x")
        self.entry_nome = tk.Entry(
            container, font=FONTE_CAMPO,
            bg=COR_FUNDO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        self.entry_nome.pack(fill="x", pady=(2, 0))
        tk.Frame(container, bg=COR_BORDA, height=1).pack(fill="x", pady=(0, 10))

        tk.Label(
            container, text="descricao", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE, anchor="w",
        ).pack(fill="x", pady=(0, 2))
        self.text_desc = tk.Text(
            container, height=6,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
            padx=8, pady=6, font=FONTE_LABEL, wrap="word",
            highlightthickness=1, highlightbackground=COR_BORDA,
        )
        self.text_desc.pack(fill="both", expand=True, pady=(0, 12))

        rodape = tk.Frame(container, bg=COR_FUNDO)
        rodape.pack(fill="x")

        cancelar = tk.Label(
            rodape, text="Cancelar", font=FONTE_BOTAO,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE,
            cursor="hand2", padx=14, pady=6,
        )
        cancelar.pack(side="right", padx=(0, 8))
        cancelar.bind("<Button-1>", lambda e: self.destroy())
        cancelar.bind("<Enter>", lambda e: cancelar.configure(fg=COR_TEXTO))
        cancelar.bind("<Leave>", lambda e: cancelar.configure(fg=COR_TEXTO_SUAVE))

        criar = tk.Label(
            rodape, text="Criar", font=FONTE_BOTAO,
            bg=COR_DESTAQUE, fg=COR_TEXTO,
            cursor="hand2", padx=20, pady=6,
        )
        criar.pack(side="right")
        criar.bind("<Button-1>", lambda e: self._confirmar())
        criar.bind("<Enter>", lambda e: criar.configure(bg=COR_DESTAQUE_HOVER))
        criar.bind("<Leave>", lambda e: criar.configure(bg=COR_DESTAQUE))

        self.entry_nome.focus_set()

    def _confirmar(self):
        nome = self.entry_nome.get().strip()
        if not nome:
            messagebox.showwarning(
                "Atencao", "O nome da habilidade e obrigatorio.", parent=self,
            )
            return
        descricao = self.text_desc.get("1.0", "end").strip()
        self.resultado = (nome, descricao)
        self.destroy()


class TelaCriacaoPersonagem(tk.Toplevel):
    TAMANHO_IMAGEM = 150
    LARGURA = 828
    ALTURA = 680

    def __init__(self, master, criado_por, personagem_existente=None):
        super().__init__(master)
        self.criado_por = criado_por
        self.existente = personagem_existente
        self.modo_edicao = personagem_existente is not None

        self.imagem_origem = None
        self.imagem_path_salvo = ""
        self.imagem_tk = None
        self.nivel_lc = None
        self.botoes_lc = []

        self.atributos = {nome: 0 for nome in ATRIBUTOS_NOMES}
        self.labels_atributos = {}

        self.armamentos = []
        self.itens = []
        self.habilidades = []
        self.catalogo_habilidades = []
        self.maestrias = {
            "elementais": {nome: 0 for nome in MAESTRIAS_ELEMENTAIS},
            "primordiais": {nome: 0 for nome in MAESTRIAS_PRIMORDIAIS},
        }
        self.labels_maestrias = {"elementais": {}, "primordiais": {}}
        self.aba_atual = "personagem"
        self.tab_labels = {}
        self.frames_aba = {}

        self.vida_maxima = calcular_vida_maxima(None, 0)
        self.vida_atual = self.vida_maxima
        self.energia_maxima = calcular_energia_maxima(None, 0)
        self.energia_atual = self.energia_maxima
        self.sanidade = SANIDADE_INICIAL

        self.title("Editar Personagem" if self.modo_edicao else "Criar Personagem")
        self.configure(bg=COR_FUNDO)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._centralizar()
        self._carregar_catalogo_habilidades()
        self._montar_interface()

        if self.modo_edicao:
            self._preencher_com_existente()

    def _centralizar(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.LARGURA // 2)
        y = (self.winfo_screenheight() // 2) - (self.ALTURA // 2)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{x}+{y}")

    def _montar_interface(self):
        container = tk.Frame(self, bg=COR_FUNDO)
        container.pack(expand=True, fill="both", padx=24, pady=12)

        tk.Label(
            container,
            text="Editar Personagem" if self.modo_edicao else "Novo Personagem",
            font=FONTE_SECAO,
            bg=COR_FUNDO,
            fg=COR_TEXTO,
        ).pack(anchor="w", pady=(0, 6))

        self._montar_abas(container)

        corpo_abas = tk.Frame(container, bg=COR_FUNDO)
        corpo_abas.pack(fill="both", expand=True, pady=(8, 0))

        self.frames_aba["personagem"] = tk.Frame(corpo_abas, bg=COR_FUNDO)
        self.frames_aba["inventario"] = tk.Frame(corpo_abas, bg=COR_FUNDO)
        self.frames_aba["habilidades"] = tk.Frame(corpo_abas, bg=COR_FUNDO)
        self.frames_aba["maestrias"] = tk.Frame(corpo_abas, bg=COR_FUNDO)

        self._montar_aba_personagem(self.frames_aba["personagem"])
        self._montar_aba_inventario(self.frames_aba["inventario"])
        self._montar_aba_habilidades(self.frames_aba["habilidades"])
        self._montar_aba_maestrias(self.frames_aba["maestrias"])

        self._montar_rodape(container)
        self._trocar_aba("personagem")

    def _montar_abas(self, parent):
        barra = tk.Frame(parent, bg=COR_FUNDO)
        barra.pack(fill="x")

        for chave, rotulo in (
            ("personagem", "Personagem"),
            ("inventario", "Inventario"),
            ("habilidades", "Habilidades"),
            ("maestrias", "Maestrias"),
        ):
            label = tk.Label(
                barra, text=rotulo, font=FONTE_BOTAO,
                bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
                padx=14, pady=5, cursor="hand2",
            )
            label.pack(side="left", padx=(0, 4))
            label.bind("<Button-1>", lambda e, c=chave: self._trocar_aba(c))
            self.tab_labels[chave] = label

        sublinha = tk.Frame(parent, bg=COR_BORDA, height=1)
        sublinha.pack(fill="x")

    def _trocar_aba(self, chave):
        self.aba_atual = chave
        for nome, label in self.tab_labels.items():
            if nome == chave:
                label.configure(bg=COR_DESTAQUE, fg=COR_TEXTO)
            else:
                label.configure(bg=COR_FUNDO_CAMPO, fg=COR_TEXTO)
        for nome, frame in self.frames_aba.items():
            if nome == chave:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    def _montar_aba_personagem(self, parent):
        self.canvas_personagem = tk.Canvas(
            parent, bg=COR_FUNDO, highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(parent, orient="vertical",
                                 command=self.canvas_personagem.yview)
        self.canvas_personagem.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas_personagem.pack(side="left", fill="both", expand=True)

        self.frame_personagem_conteudo = tk.Frame(self.canvas_personagem, bg=COR_FUNDO)
        self.janela_personagem = self.canvas_personagem.create_window(
            (0, 0), window=self.frame_personagem_conteudo, anchor="nw",
        )

        def _ajustar_largura(event):
            self.canvas_personagem.itemconfigure(self.janela_personagem, width=event.width)

        self.canvas_personagem.bind("<Configure>", _ajustar_largura)
        self.frame_personagem_conteudo.bind(
            "<Configure>",
            lambda e: self.canvas_personagem.configure(scrollregion=self.canvas_personagem.bbox("all")),
        )
        self.canvas_personagem.bind("<Enter>", lambda e: self._ligar_scroll_personagem())
        self.canvas_personagem.bind("<Leave>", lambda e: self._desligar_scroll_personagem())

        conteudo = self.frame_personagem_conteudo

        topo = tk.Frame(conteudo, bg=COR_FUNDO)
        topo.pack(fill="x")

        coluna_esq = tk.Frame(topo, bg=COR_FUNDO)
        coluna_esq.pack(side="left", padx=(0, 24), anchor="n")

        coluna_dir = tk.Frame(topo, bg=COR_FUNDO)
        coluna_dir.pack(side="left", fill="both", expand=True, anchor="n")

        self._montar_imagem(coluna_esq)
        self._montar_campos(coluna_dir)

        self._montar_barras(conteudo)
        self._montar_atributos(conteudo)
        self._montar_descricao(conteudo)

    def _ligar_scroll_personagem(self):
        self.canvas_personagem.bind_all("<MouseWheel>", self._scroll_personagem)

    def _desligar_scroll_personagem(self):
        self.canvas_personagem.unbind_all("<MouseWheel>")

    def _scroll_personagem(self, event):
        self.canvas_personagem.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _montar_descricao(self, parent):
        secao = tk.Frame(parent, bg=COR_FUNDO)
        secao.pack(fill="x", pady=(12, 0))

        tk.Label(
            secao, text="DESCRICAO / HISTORIA", font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.text_descricao = tk.Text(
            secao, height=6,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO,
            relief="flat", bd=0, padx=8, pady=6,
            font=FONTE_LABEL, wrap="word",
            highlightthickness=1, highlightbackground=COR_BORDA,
        )
        self.text_descricao.pack(fill="x")

    # ----- imagem -----

    def _montar_imagem(self, parent):
        self.quadro_imagem = tk.Frame(
            parent,
            bg=COR_FUNDO_CAMPO,
            width=self.TAMANHO_IMAGEM,
            height=self.TAMANHO_IMAGEM,
            highlightthickness=1,
            highlightbackground=COR_BORDA,
        )
        self.quadro_imagem.pack()
        self.quadro_imagem.pack_propagate(False)

        self.label_imagem = tk.Label(
            self.quadro_imagem,
            text="clique para\nescolher imagem",
            font=FONTE_LABEL,
            bg=COR_FUNDO_CAMPO,
            fg=COR_TEXTO_SUAVE,
            cursor="hand2",
        )
        self.label_imagem.pack(expand=True, fill="both")
        self.label_imagem.bind("<Button-1>", lambda e: self._escolher_imagem())

        tk.Label(
            parent,
            text="imagem do personagem",
            font=FONTE_LABEL,
            bg=COR_FUNDO,
            fg=COR_TEXTO_FRACO,
        ).pack(pady=(4, 0))

    def _escolher_imagem(self):
        caminho = filedialog.askopenfilename(
            parent=self,
            title="Escolher imagem",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return
        try:
            img = Image.open(caminho)
            img.thumbnail((self.TAMANHO_IMAGEM, self.TAMANHO_IMAGEM), Image.LANCZOS)
            self.imagem_tk = ImageTk.PhotoImage(img)
            self.label_imagem.configure(image=self.imagem_tk, text="")
            self.imagem_origem = caminho
        except Exception as erro:
            messagebox.showerror("Erro", f"Nao foi possivel carregar a imagem:\n{erro}", parent=self)

    # ----- campos -----

    def _montar_campos(self, parent):
        self.campo_nome = self._criar_campo_texto(parent, "nome")
        self.campo_idade = self._criar_campo_texto(parent, "idade")

        self.campos_nasc = self._criar_campo_data(parent, "nascimento")
        self.campos_crist = self._criar_campo_data(parent, "data de cristalizacao")

        self._montar_lc(parent)

    def _criar_campo_texto(self, parent, rotulo):
        tk.Label(
            parent, text=rotulo, font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE, anchor="w",
        ).pack(fill="x", pady=(4, 1))

        entrada = tk.Entry(
            parent, font=FONTE_CAMPO,
            bg=COR_FUNDO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entrada.pack(fill="x")

        linha = tk.Frame(parent, bg=COR_BORDA, height=1)
        linha.pack(fill="x")
        entrada.bind("<FocusIn>", lambda e: linha.configure(bg=COR_DESTAQUE))
        entrada.bind("<FocusOut>", lambda e: linha.configure(bg=COR_BORDA))
        return entrada

    def _criar_campo_data(self, parent, rotulo):
        tk.Label(
            parent, text=rotulo, font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE, anchor="w",
        ).pack(fill="x", pady=(4, 1))

        linha_campos = tk.Frame(parent, bg=COR_FUNDO)
        linha_campos.pack(fill="x")

        partes = []
        for i, (placeholder, largura) in enumerate(
            [("DD", 3), ("MM", 3), ("AA", 3)]
        ):
            entrada = tk.Entry(
                linha_campos, font=FONTE_CAMPO, width=largura,
                bg=COR_FUNDO, fg=COR_TEXTO,
                insertbackground=COR_TEXTO, relief="flat", bd=0,
                justify="center",
            )
            entrada.insert(0, placeholder)
            entrada.configure(fg=COR_TEXTO_FRACO)
            entrada.bind("<FocusIn>", lambda e, ent=entrada, ph=placeholder: self._limpar_placeholder(ent, ph))
            entrada.bind("<FocusOut>", lambda e, ent=entrada, ph=placeholder: self._restaurar_placeholder(ent, ph))
            entrada.pack(side="left", padx=(0, 4))
            partes.append(entrada)
            if i < 2:
                tk.Label(
                    linha_campos, text="/", font=FONTE_CAMPO,
                    bg=COR_FUNDO, fg=COR_TEXTO_SUAVE,
                ).pack(side="left", padx=(0, 4))

        sublinha = tk.Frame(parent, bg=COR_BORDA, height=1)
        sublinha.pack(fill="x", pady=(2, 0))
        return partes

    def _limpar_placeholder(self, entrada, placeholder):
        if entrada.get() == placeholder:
            entrada.delete(0, tk.END)
            entrada.configure(fg=COR_TEXTO)

    def _restaurar_placeholder(self, entrada, placeholder):
        if not entrada.get().strip():
            entrada.insert(0, placeholder)
            entrada.configure(fg=COR_TEXTO_FRACO)

    def _ler_data(self, partes):
        valores = []
        for ent, ph in zip(partes, ("DD", "MM", "AA")):
            valor = ent.get().strip()
            if valor == ph:
                valor = ""
            valores.append(valor)
        if not any(valores):
            return ""
        return "/".join(v.zfill(2) if v else "--" for v in valores)

    # ----- nivel de LC -----

    def _montar_lc(self, parent):
        tk.Label(
            parent, text="nivel de LC", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE, anchor="w",
        ).pack(fill="x", pady=(8, 3))

        grade = tk.Frame(parent, bg=COR_FUNDO)
        grade.pack(anchor="w")

        for nivel in range(11):
            botao = tk.Label(
                grade,
                text=f"LC {nivel}",
                font=FONTE_LABEL,
                bg=COR_FUNDO_CAMPO,
                fg=COR_TEXTO,
                width=5, padx=4, pady=4,
                cursor="hand2",
            )
            botao.grid(row=0, column=nivel, padx=2)
            botao.bind("<Button-1>", lambda e, n=nivel: self._selecionar_lc(n))
            self.botoes_lc.append(botao)

    def _selecionar_lc(self, nivel):
        self.nivel_lc = nivel
        for i, botao in enumerate(self.botoes_lc):
            if i == nivel:
                botao.configure(bg=COR_DESTAQUE, fg=COR_TEXTO)
            else:
                botao.configure(bg=COR_FUNDO_CAMPO, fg=COR_TEXTO)
        self._recalcular_maximos(reiniciar_atual=True)

    # ----- barras (vida / energia / sanidade) -----

    def _montar_barras(self, parent):
        bloco = tk.Frame(parent, bg=COR_FUNDO)
        bloco.pack(fill="x", pady=(10, 0))

        for i in range(3):
            bloco.grid_columnconfigure(i, weight=1, uniform="barras")

        self.barras = {}

        col_vida = tk.Frame(bloco, bg=COR_FUNDO)
        col_vida.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._criar_barra(col_vida, chave="vida", rotulo="VIDA",
                          cor=COR_VIDA, cor_fundo=COR_VIDA_FUNDO,
                          tem_maxima_editavel=False)

        col_energia = tk.Frame(bloco, bg=COR_FUNDO)
        col_energia.grid(row=0, column=1, sticky="nsew", padx=6)
        self._criar_barra(col_energia, chave="energia", rotulo="ENERGIA",
                          cor=COR_ENERGIA, cor_fundo=COR_ENERGIA_FUNDO,
                          tem_maxima_editavel=False)

        col_sanidade = tk.Frame(bloco, bg=COR_FUNDO)
        col_sanidade.grid(row=0, column=2, sticky="nsew", padx=(12, 0))
        self._criar_barra(col_sanidade, chave="sanidade", rotulo="SANIDADE",
                          cor=COR_SANIDADE, cor_fundo=COR_SANIDADE_FUNDO,
                          tem_maxima_editavel=False)

    def _criar_barra(self, parent, chave, rotulo, cor, cor_fundo, tem_maxima_editavel):
        tk.Label(
            parent, text=rotulo, font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO, fg=cor, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        linha = tk.Frame(parent, bg=COR_FUNDO)
        linha.pack(fill="x")

        seta_esq = tk.Label(
            linha, text="\u25c0", font=("Segoe UI", 12),
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE, cursor="hand2", padx=6,
        )
        seta_esq.pack(side="left")
        seta_esq.bind("<Button-1>", lambda e, c=chave: self._ajustar_barra(c, -1))

        seta_dir = tk.Label(
            linha, text="\u25b6", font=("Segoe UI", 12),
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE, cursor="hand2", padx=6,
        )
        seta_dir.pack(side="right")
        seta_dir.bind("<Button-1>", lambda e, c=chave: self._ajustar_barra(c, 1))

        meio = tk.Frame(linha, bg=COR_FUNDO)
        meio.pack(side="left", expand=True, fill="x", padx=4)

        canvas = tk.Canvas(
            meio, height=20, bg=cor_fundo,
            highlightthickness=1, highlightbackground=COR_BORDA,
        )
        canvas.pack(fill="x")
        retangulo = canvas.create_rectangle(0, 0, 0, 20, fill=cor, outline="")

        controles = tk.Frame(parent, bg=COR_FUNDO)
        controles.pack(fill="x", pady=(6, 0))

        label = tk.Label(
            controles, text="", font=FONTE_DISCRETA,
            bg=COR_FUNDO, fg=COR_TEXTO,
        )
        label.pack(side="left")

        tk.Label(
            controles, text="atual", font=FONTE_LABEL,
            bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(12, 2))

        entry_atual = tk.Entry(
            controles, font=FONTE_LABEL, width=4, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_atual.pack(side="left")

        entry_maxima = None
        if tem_maxima_editavel:
            tk.Label(
                controles, text="max", font=FONTE_LABEL,
                bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
            ).pack(side="left", padx=(8, 2))
            entry_maxima = tk.Entry(
                controles, font=FONTE_LABEL, width=4, justify="center",
                bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
                insertbackground=COR_TEXTO, relief="flat", bd=0,
            )
            entry_maxima.pack(side="left")

        self.barras[chave] = {
            "canvas": canvas,
            "retangulo": retangulo,
            "label": label,
            "entry_atual": entry_atual,
            "entry_maxima": entry_maxima,
        }

        entry_atual.bind("<FocusOut>", lambda e, c=chave: self._sincronizar_barra(c))
        entry_atual.bind("<Return>", lambda e, c=chave: self._sincronizar_barra(c))
        if entry_maxima is not None:
            entry_maxima.bind("<FocusOut>", lambda e, c=chave: self._sincronizar_barra(c, max_alterado=True))
            entry_maxima.bind("<Return>", lambda e, c=chave: self._sincronizar_barra(c, max_alterado=True))

        canvas.bind("<Configure>", lambda e, c=chave: self._desenhar_barra(c))
        self._atualizar_entries(chave)
        self._desenhar_barra(chave)

    def _valores_barra(self, chave):
        if chave == "vida":
            return self.vida_atual, self.vida_maxima
        if chave == "energia":
            return self.energia_atual, self.energia_maxima
        return self.sanidade, SANIDADE_MAX

    def _set_barra(self, chave, atual=None, maxima=None):
        if chave == "vida":
            if maxima is not None:
                self.vida_maxima = max(1, maxima)
            if atual is not None:
                self.vida_atual = max(0, min(self.vida_maxima, atual))
        elif chave == "energia":
            if maxima is not None:
                self.energia_maxima = max(1, maxima)
            if atual is not None:
                self.energia_atual = max(0, min(self.energia_maxima, atual))
        else:
            if atual is not None:
                self.sanidade = max(0, min(SANIDADE_MAX, atual))

    def _ajustar_barra(self, chave, delta):
        atual, _ = self._valores_barra(chave)
        self._set_barra(chave, atual=atual + delta)
        self._atualizar_entries(chave)
        self._desenhar_barra(chave)

    def _sincronizar_barra(self, chave, max_alterado=False):
        info = self.barras[chave]
        try:
            atual = int(info["entry_atual"].get())
        except ValueError:
            atual, _ = self._valores_barra(chave)
        maxima = None
        if max_alterado and info["entry_maxima"] is not None:
            try:
                maxima = int(info["entry_maxima"].get())
            except ValueError:
                maxima = None
        self._set_barra(chave, atual=atual, maxima=maxima)
        self._atualizar_entries(chave)
        self._desenhar_barra(chave)

    def _atualizar_entries(self, chave):
        atual, maxima = self._valores_barra(chave)
        info = self.barras[chave]
        info["entry_atual"].delete(0, tk.END)
        info["entry_atual"].insert(0, str(atual))
        if info["entry_maxima"] is not None:
            info["entry_maxima"].delete(0, tk.END)
            info["entry_maxima"].insert(0, str(maxima))

    def _desenhar_barra(self, chave):
        info = self.barras[chave]
        canvas = info["canvas"]
        atual, maxima = self._valores_barra(chave)
        largura = max(1, canvas.winfo_width())
        altura = canvas.winfo_height() or 20
        proporcao = 0 if maxima <= 0 else atual / maxima
        proporcao = max(0.0, min(1.0, proporcao))
        canvas.coords(info["retangulo"], 0, 0, largura * proporcao, altura)
        if chave == "sanidade":
            info["label"].configure(text=f"{atual}%  / {maxima}%")
        else:
            info["label"].configure(text=f"{atual} / {maxima}")

    def _recalcular_maximos(self, reiniciar_atual=False):
        nova_vida = calcular_vida_maxima(self.nivel_lc, self.atributos.get("VITALIDADE", 0))
        nova_energia = calcular_energia_maxima(self.nivel_lc, self.atributos.get("PRESENCA", 0))
        self.vida_maxima = nova_vida
        self.energia_maxima = nova_energia
        if reiniciar_atual:
            self.vida_atual = nova_vida
            self.energia_atual = nova_energia
        else:
            self.vida_atual = min(self.vida_atual, nova_vida)
            self.energia_atual = min(self.energia_atual, nova_energia)
        if hasattr(self, "barras"):
            for chave in ("vida", "energia"):
                self._atualizar_entries(chave)
                self._desenhar_barra(chave)

    # ----- atributos -----

    def _montar_atributos(self, parent):
        secao = tk.Frame(parent, bg=COR_FUNDO)
        secao.pack(fill="x", pady=(12, 0))

        tk.Label(
            secao, text="ATRIBUTOS", font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        grade = tk.Frame(secao, bg=COR_FUNDO)
        grade.pack(fill="x")

        colunas = 3
        for c in range(colunas):
            grade.grid_columnconfigure(c, weight=1, uniform="atrs")

        for idx, nome in enumerate(ATRIBUTOS_NOMES):
            linha = idx // colunas
            coluna = idx % colunas
            self._criar_celula_atributo(grade, nome).grid(
                row=linha, column=coluna, padx=4, pady=3, sticky="nsew",
            )

    def _criar_celula_atributo(self, parent, nome):
        celula = tk.Frame(parent, bg=COR_FUNDO_PAINEL,
                          highlightthickness=1, highlightbackground=COR_BORDA)

        rotulo = nome
        if nome == "PRESENCA":
            rotulo = f"PRESENCA  +{BONUS_PRESENCA} energia"
        elif nome == "VITALIDADE":
            rotulo = f"VITALIDADE  +{BONUS_VITALIDADE} vida"

        tk.Label(
            celula, text=rotulo, font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE,
        ).pack(pady=(5, 2))

        controle = tk.Frame(celula, bg=COR_FUNDO_PAINEL)
        controle.pack(pady=(0, 5))

        menos = tk.Label(
            controle, text="\u2212", font=("Segoe UI", 12, "bold"),
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO, width=2, cursor="hand2",
        )
        menos.pack(side="left", padx=(0, 6))
        menos.bind("<Button-1>", lambda e, n=nome: self._ajustar_atributo(n, -1))

        valor = tk.Label(
            controle, text="0", font=("Segoe UI", 14),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, width=3,
        )
        valor.pack(side="left")
        self.labels_atributos[nome] = valor

        mais = tk.Label(
            controle, text="+", font=("Segoe UI", 12, "bold"),
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO, width=2, cursor="hand2",
        )
        mais.pack(side="left", padx=(6, 0))
        mais.bind("<Button-1>", lambda e, n=nome: self._ajustar_atributo(n, 1))

        return celula

    def _ajustar_atributo(self, nome, delta):
        novo = max(0, self.atributos[nome] + delta)
        self.atributos[nome] = novo
        self.labels_atributos[nome].configure(text=str(novo))
        if nome in ("PRESENCA", "VITALIDADE"):
            self._recalcular_maximos(reiniciar_atual=False)

    # ----- aba inventario -----

    def _montar_aba_inventario(self, parent):
        moldura = tk.Frame(parent, bg=COR_FUNDO,
                           highlightthickness=1, highlightbackground=COR_BORDA)
        moldura.pack(fill="both", expand=True)

        self.canvas_armas = tk.Canvas(
            moldura, bg=COR_FUNDO, highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(moldura, orient="vertical",
                                 command=self.canvas_armas.yview)
        self.canvas_armas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas_armas.pack(side="left", fill="both", expand=True)

        self.frame_inventario = tk.Frame(self.canvas_armas, bg=COR_FUNDO)
        self.janela_armas = self.canvas_armas.create_window(
            (0, 0), window=self.frame_inventario, anchor="nw",
        )

        def _ajustar_largura(event):
            self.canvas_armas.itemconfigure(self.janela_armas, width=event.width)

        self.canvas_armas.bind("<Configure>", _ajustar_largura)
        self.frame_inventario.bind(
            "<Configure>",
            lambda e: self.canvas_armas.configure(scrollregion=self.canvas_armas.bbox("all")),
        )
        self.canvas_armas.bind("<Enter>", lambda e: self._ligar_scroll_armas())
        self.canvas_armas.bind("<Leave>", lambda e: self._desligar_scroll_armas())

        self._renderizar_inventario()

    def _ligar_scroll_armas(self):
        self.canvas_armas.bind_all("<MouseWheel>", self._scroll_armas)

    def _desligar_scroll_armas(self):
        self.canvas_armas.unbind_all("<MouseWheel>")

    def _scroll_armas(self, event):
        self.canvas_armas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _adicionar_arma(self):
        self.armamentos.append({
            "id": uuid.uuid4().hex,
            "nome": "",
            "tipo": TIPO_ARMA_PADRAO,
            "dano": "",
            "municao_atual": 0,
            "municao_maxima": 0,
            "descricao": "",
        })
        self._renderizar_inventario()

    def _remover_arma(self, arma_id):
        self.armamentos = [a for a in self.armamentos if a.get("id") != arma_id]
        self._renderizar_inventario()

    def _adicionar_item(self):
        self.itens.append({
            "id": uuid.uuid4().hex,
            "tipo": TIPO_ITEM_PADRAO,
            "nome": "",
            "quantidade": 1,
            "descricao": "",
        })
        self._renderizar_inventario()

    def _remover_item(self, item_id):
        self.itens = [i for i in self.itens if i.get("id") != item_id]
        self._renderizar_inventario()

    def _renderizar_inventario(self):
        for child in self.frame_inventario.winfo_children():
            child.destroy()

        # ----- secao armas -----
        self._cabecalho_secao(
            self.frame_inventario, "ARMAS", "+ Adicionar arma",
            self._adicionar_arma,
        )
        if not self.armamentos:
            tk.Label(
                self.frame_inventario, text="nenhuma arma cadastrada",
                font=FONTE_LABEL, bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
            ).pack(anchor="w", padx=14, pady=(0, 4))
        for arma in self.armamentos:
            self._criar_card_arma(self.frame_inventario, arma).pack(
                fill="x", padx=8, pady=4,
            )

        # ----- secao itens -----
        self._cabecalho_secao(
            self.frame_inventario, "ITENS", "+ Adicionar item",
            self._adicionar_item, pady_topo=(16, 4),
        )
        if not self.itens:
            tk.Label(
                self.frame_inventario, text="nenhum item cadastrado",
                font=FONTE_LABEL, bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
            ).pack(anchor="w", padx=14, pady=(0, 4))
        for item in self.itens:
            self._criar_card_item(self.frame_inventario, item).pack(
                fill="x", padx=8, pady=4,
            )

    def _cabecalho_secao(self, parent, titulo, texto_botao, callback, pady_topo=(4, 4)):
        cab = tk.Frame(parent, bg=COR_FUNDO)
        cab.pack(fill="x", padx=8, pady=pady_topo)

        tk.Label(
            cab, text=titulo, font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO,
        ).pack(side="left")

        botao = tk.Label(
            cab, text=texto_botao, font=FONTE_BOTAO,
            bg=COR_DESTAQUE, fg=COR_TEXTO,
            padx=10, pady=4, cursor="hand2",
        )
        botao.pack(side="right")
        botao.bind("<Button-1>", lambda e: callback())
        botao.bind("<Enter>", lambda e: botao.configure(bg=COR_DESTAQUE_HOVER))
        botao.bind("<Leave>", lambda e: botao.configure(bg=COR_DESTAQUE))

    def _criar_card_arma(self, parent, arma):
        card = tk.Frame(parent, bg=COR_FUNDO_PAINEL,
                        highlightthickness=1, highlightbackground=COR_BORDA)

        # linha 1: nome + excluir
        linha1 = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha1.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(
            linha1, text="nome", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        entry_nome = tk.Entry(
            linha1, font=FONTE_CAMPO,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_nome.insert(0, arma.get("nome", ""))
        entry_nome.pack(side="left", fill="x", expand=True, padx=(0, 8))
        entry_nome.bind("<KeyRelease>", lambda e, a=arma: a.update({"nome": entry_nome.get()}))

        excluir = tk.Label(
            linha1, text="\u2715", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2",
        )
        excluir.pack(side="right")
        excluir.bind("<Button-1>", lambda e, aid=arma["id"]: self._remover_arma(aid))
        excluir.bind("<Enter>", lambda e: excluir.configure(fg=COR_VIDA))
        excluir.bind("<Leave>", lambda e: excluir.configure(fg=COR_TEXTO_SUAVE))

        # linha 2: tipo + dano
        linha2 = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha2.pack(fill="x", padx=10, pady=(0, 4))

        tk.Label(
            linha2, text="tipo", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        var_tipo = tk.StringVar(value=arma.get("tipo", TIPO_ARMA_PADRAO))
        menu_tipo = tk.OptionMenu(
            linha2, var_tipo, *TIPOS_ARMA,
            command=lambda valor, a=arma: self._on_tipo_arma_changed(a, valor),
        )
        menu_tipo.configure(
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            activebackground=COR_DESTAQUE, activeforeground=COR_TEXTO,
            relief="flat", bd=0, font=FONTE_LABEL, highlightthickness=0,
        )
        menu_tipo["menu"].configure(
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            activebackground=COR_DESTAQUE, activeforeground=COR_TEXTO,
        )
        menu_tipo.pack(side="left", padx=(0, 16))

        tk.Label(
            linha2, text="dano", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        entry_dano = tk.Entry(
            linha2, font=FONTE_CAMPO, width=10,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_dano.insert(0, arma.get("dano", ""))
        entry_dano.pack(side="left")
        entry_dano.bind("<KeyRelease>", lambda e, a=arma: a.update({"dano": entry_dano.get()}))

        tk.Label(
            linha2, text=DICA_DANO, font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(8, 0))

        # linha 3: municao (so para armas de fogo)
        bloco_municao = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        if arma["tipo"] in TIPOS_COM_MUNICAO:
            self._montar_linha_municao(bloco_municao, arma)
            bloco_municao.pack(fill="x", padx=10, pady=(0, 4))

        # linha 4: descricao
        linha4 = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha4.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(
            linha4, text="descricao", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        entry_desc = tk.Entry(
            linha4, font=FONTE_LABEL,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_desc.insert(0, arma.get("descricao", ""))
        entry_desc.pack(side="left", fill="x", expand=True)
        entry_desc.bind("<KeyRelease>", lambda e, a=arma: a.update({"descricao": entry_desc.get()}))

        return card

    def _montar_linha_municao(self, parent, arma):
        tk.Label(
            parent, text="municao", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        seta_esq = tk.Label(
            parent, text="\u25c0", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2", padx=4,
        )
        seta_esq.pack(side="left")

        entry_atual = tk.Entry(
            parent, font=FONTE_LABEL, width=4, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_atual.insert(0, str(int(arma.get("municao_atual", 0) or 0)))
        entry_atual.pack(side="left", padx=2)

        tk.Label(
            parent, text="/", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left")

        entry_max = tk.Entry(
            parent, font=FONTE_LABEL, width=4, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_max.insert(0, str(int(arma.get("municao_maxima", 0) or 0)))
        entry_max.pack(side="left", padx=2)

        seta_dir = tk.Label(
            parent, text="\u25b6", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2", padx=4,
        )
        seta_dir.pack(side="left")

        def sincronizar():
            try:
                atual = int(entry_atual.get())
            except ValueError:
                atual = int(arma.get("municao_atual", 0) or 0)
            try:
                maxima = max(0, int(entry_max.get()))
            except ValueError:
                maxima = int(arma.get("municao_maxima", 0) or 0)
            atual = max(0, min(maxima, atual))
            arma["municao_atual"] = atual
            arma["municao_maxima"] = maxima
            entry_atual.delete(0, tk.END)
            entry_atual.insert(0, str(atual))
            entry_max.delete(0, tk.END)
            entry_max.insert(0, str(maxima))

        def ajustar(delta):
            try:
                atual = int(entry_atual.get())
            except ValueError:
                atual = int(arma.get("municao_atual", 0) or 0)
            entry_atual.delete(0, tk.END)
            entry_atual.insert(0, str(atual + delta))
            sincronizar()

        seta_esq.bind("<Button-1>", lambda e: ajustar(-1))
        seta_dir.bind("<Button-1>", lambda e: ajustar(1))
        for ent in (entry_atual, entry_max):
            ent.bind("<FocusOut>", lambda e: sincronizar())
            ent.bind("<Return>", lambda e: sincronizar())

    def _on_tipo_arma_changed(self, arma, novo_tipo):
        arma["tipo"] = novo_tipo
        if novo_tipo not in TIPOS_COM_MUNICAO:
            arma["municao_atual"] = 0
            arma["municao_maxima"] = 0
        self._renderizar_inventario()

    def _criar_card_item(self, parent, item):
        card = tk.Frame(parent, bg=COR_FUNDO_PAINEL,
                        highlightthickness=1, highlightbackground=COR_BORDA)

        # linha 1: tipo + nome + excluir
        linha1 = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha1.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(
            linha1, text="tipo", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        var_tipo = tk.StringVar(value=item.get("tipo", TIPO_ITEM_PADRAO))
        menu_tipo = tk.OptionMenu(
            linha1, var_tipo, *TIPOS_ITEM,
            command=lambda valor, it=item: it.update({"tipo": valor}),
        )
        menu_tipo.configure(
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            activebackground=COR_DESTAQUE, activeforeground=COR_TEXTO,
            relief="flat", bd=0, font=FONTE_LABEL, highlightthickness=0,
        )
        menu_tipo["menu"].configure(
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            activebackground=COR_DESTAQUE, activeforeground=COR_TEXTO,
        )
        menu_tipo.pack(side="left", padx=(0, 16))

        tk.Label(
            linha1, text="nome", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        entry_nome = tk.Entry(
            linha1, font=FONTE_CAMPO,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_nome.insert(0, item.get("nome", ""))
        entry_nome.pack(side="left", fill="x", expand=True, padx=(0, 8))
        entry_nome.bind("<KeyRelease>", lambda e, it=item: it.update({"nome": entry_nome.get()}))

        excluir = tk.Label(
            linha1, text="\u2715", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2",
        )
        excluir.pack(side="right")
        excluir.bind("<Button-1>", lambda e, iid=item["id"]: self._remover_item(iid))
        excluir.bind("<Enter>", lambda e: excluir.configure(fg=COR_VIDA))
        excluir.bind("<Leave>", lambda e: excluir.configure(fg=COR_TEXTO_SUAVE))

        # linha 2: quantidade + descricao
        linha2 = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha2.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(
            linha2, text="qtd", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 4))

        entry_qtd = tk.Entry(
            linha2, font=FONTE_LABEL, width=4, justify="center",
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_qtd.insert(0, str(int(item.get("quantidade", 1) or 0)))
        entry_qtd.pack(side="left", padx=(0, 16))

        def sincronizar_qtd():
            try:
                v = max(0, int(entry_qtd.get()))
            except ValueError:
                v = int(item.get("quantidade", 1) or 0)
            item["quantidade"] = v
            entry_qtd.delete(0, tk.END)
            entry_qtd.insert(0, str(v))

        entry_qtd.bind("<FocusOut>", lambda e: sincronizar_qtd())
        entry_qtd.bind("<Return>", lambda e: sincronizar_qtd())

        tk.Label(
            linha2, text="descricao", font=FONTE_LABEL,
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
        ).pack(side="left", padx=(0, 6))

        entry_desc = tk.Entry(
            linha2, font=FONTE_LABEL,
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO,
            insertbackground=COR_TEXTO, relief="flat", bd=0,
        )
        entry_desc.insert(0, item.get("descricao", ""))
        entry_desc.pack(side="left", fill="x", expand=True)
        entry_desc.bind("<KeyRelease>", lambda e, it=item: it.update({"descricao": entry_desc.get()}))

        return card

    # ----- aba habilidades -----

    def _carregar_catalogo_habilidades(self):
        try:
            self.catalogo_habilidades = list(carregar_habilidades() or [])
        except Exception:
            self.catalogo_habilidades = []

    def _montar_aba_habilidades(self, parent):
        moldura = tk.Frame(parent, bg=COR_FUNDO,
                           highlightthickness=1, highlightbackground=COR_BORDA)
        moldura.pack(fill="both", expand=True)

        self.canvas_habilidades = tk.Canvas(
            moldura, bg=COR_FUNDO, highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(moldura, orient="vertical",
                                 command=self.canvas_habilidades.yview)
        self.canvas_habilidades.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas_habilidades.pack(side="left", fill="both", expand=True)

        self.frame_habilidades = tk.Frame(self.canvas_habilidades, bg=COR_FUNDO)
        janela = self.canvas_habilidades.create_window(
            (0, 0), window=self.frame_habilidades, anchor="nw",
        )

        self.canvas_habilidades.bind(
            "<Configure>",
            lambda e: self.canvas_habilidades.itemconfigure(janela, width=e.width),
        )
        self.frame_habilidades.bind(
            "<Configure>",
            lambda e: self.canvas_habilidades.configure(
                scrollregion=self.canvas_habilidades.bbox("all")
            ),
        )
        self.canvas_habilidades.bind("<Enter>", lambda e: self._ligar_scroll_habilidades())
        self.canvas_habilidades.bind("<Leave>", lambda e: self._desligar_scroll_habilidades())

        self._renderizar_habilidades()

    def _ligar_scroll_habilidades(self):
        self.canvas_habilidades.bind_all("<MouseWheel>", self._scroll_habilidades)

    def _desligar_scroll_habilidades(self):
        self.canvas_habilidades.unbind_all("<MouseWheel>")

    def _scroll_habilidades(self, event):
        self.canvas_habilidades.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _renderizar_habilidades(self):
        for child in self.frame_habilidades.winfo_children():
            child.destroy()

        # ----- minhas habilidades -----
        tk.Label(
            self.frame_habilidades, text="MINHAS HABILIDADES",
            font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO, anchor="w",
        ).pack(fill="x", padx=8, pady=(4, 4))

        if not self.habilidades:
            tk.Label(
                self.frame_habilidades, text="nenhuma habilidade selecionada",
                font=FONTE_LABEL, bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
            ).pack(anchor="w", padx=14, pady=(0, 4))
        for hab in self.habilidades:
            self._criar_card_habilidade_minha(hab).pack(
                fill="x", padx=8, pady=4,
            )

        # ----- disponiveis + botao criar -----
        self._cabecalho_secao(
            self.frame_habilidades, "HABILIDADES DISPONIVEIS",
            "+ Criar habilidade", self._criar_habilidade,
            pady_topo=(16, 4),
        )

        if not self.catalogo_habilidades:
            tk.Label(
                self.frame_habilidades, text="nenhuma habilidade cadastrada",
                font=FONTE_LABEL, bg=COR_FUNDO, fg=COR_TEXTO_FRACO,
            ).pack(anchor="w", padx=14, pady=(0, 4))
        for hab in self.catalogo_habilidades:
            self._criar_card_habilidade_disponivel(hab).pack(
                fill="x", padx=8, pady=4,
            )

    def _criar_card_habilidade_minha(self, hab):
        card = tk.Frame(self.frame_habilidades, bg=COR_FUNDO_PAINEL,
                        highlightthickness=1, highlightbackground=COR_BORDA)

        linha1 = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha1.pack(fill="x", padx=10, pady=(8, 2))

        tk.Label(
            linha1, text=hab.get("nome", ""),
            font=("Segoe UI", 10, "bold"),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, anchor="w",
        ).pack(side="left", fill="x", expand=True)

        remover = tk.Label(
            linha1, text="✕", font=("Segoe UI", 11),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE, cursor="hand2",
        )
        remover.pack(side="right")
        remover.bind("<Button-1>", lambda e, hid=hab.get("id"): self._remover_habilidade(hid))
        remover.bind("<Enter>", lambda e: remover.configure(fg=COR_VIDA))
        remover.bind("<Leave>", lambda e: remover.configure(fg=COR_TEXTO_SUAVE))

        descricao = hab.get("descricao", "") or ""
        if descricao:
            tk.Label(
                card, text=descricao, font=FONTE_LABEL,
                bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE,
                anchor="w", justify="left", wraplength=680,
            ).pack(fill="x", padx=10, pady=(0, 8))
        else:
            tk.Frame(card, bg=COR_FUNDO_PAINEL, height=4).pack()

        return card

    def _criar_card_habilidade_disponivel(self, hab):
        card = tk.Frame(self.frame_habilidades, bg=COR_FUNDO_PAINEL,
                        highlightthickness=1, highlightbackground=COR_BORDA)

        linha1 = tk.Frame(card, bg=COR_FUNDO_PAINEL)
        linha1.pack(fill="x", padx=10, pady=(8, 2))

        tk.Label(
            linha1, text=hab.get("nome", ""),
            font=("Segoe UI", 10, "bold"),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ja_selecionada = any(
            h.get("id") == hab.get("id") for h in self.habilidades
        )
        if ja_selecionada:
            tk.Label(
                linha1, text="selecionada", font=FONTE_LABEL,
                bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_FRACO,
            ).pack(side="right")
        else:
            botao = tk.Label(
                linha1, text="+ Adicionar", font=FONTE_BOTAO,
                bg=COR_DESTAQUE, fg=COR_TEXTO,
                padx=10, pady=2, cursor="hand2",
            )
            botao.pack(side="right")
            botao.bind("<Button-1>", lambda e, h=hab: self._selecionar_habilidade(h))
            botao.bind("<Enter>", lambda e: botao.configure(bg=COR_DESTAQUE_HOVER))
            botao.bind("<Leave>", lambda e: botao.configure(bg=COR_DESTAQUE))

        descricao = hab.get("descricao", "") or ""
        if descricao:
            tk.Label(
                card, text=descricao, font=FONTE_LABEL,
                bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SUAVE,
                anchor="w", justify="left", wraplength=680,
            ).pack(fill="x", padx=10, pady=(0, 8))
        else:
            tk.Frame(card, bg=COR_FUNDO_PAINEL, height=4).pack()

        return card

    def _selecionar_habilidade(self, hab):
        if any(h.get("id") == hab.get("id") for h in self.habilidades):
            return
        self.habilidades.append({
            "id": hab.get("id"),
            "nome": hab.get("nome", ""),
            "descricao": hab.get("descricao", ""),
        })
        self._renderizar_habilidades()

    def _remover_habilidade(self, hid):
        self.habilidades = [h for h in self.habilidades if h.get("id") != hid]
        self._renderizar_habilidades()

    def _criar_habilidade(self):
        dialog = DialogoCriarHabilidade(self)
        self.wait_window(dialog)
        if dialog.resultado is None:
            return
        nome, descricao = dialog.resultado
        payload = {
            "id": uuid.uuid4().hex,
            "nome": nome,
            "descricao": descricao,
        }
        try:
            nova = salvar_habilidade(payload) or payload
        except Exception as erro:
            messagebox.showerror(
                "Erro",
                f"Nao foi possivel criar a habilidade:\n{erro}",
                parent=self,
            )
            return
        self.catalogo_habilidades.append(nova)
        self._selecionar_habilidade(nova)

    # ----- aba maestrias -----

    def _montar_aba_maestrias(self, parent):
        moldura = tk.Frame(parent, bg=COR_FUNDO,
                           highlightthickness=1, highlightbackground=COR_BORDA)
        moldura.pack(fill="both", expand=True)

        self.canvas_maestrias = tk.Canvas(
            moldura, bg=COR_FUNDO, highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(moldura, orient="vertical",
                                 command=self.canvas_maestrias.yview)
        self.canvas_maestrias.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas_maestrias.pack(side="left", fill="both", expand=True)

        self.frame_maestrias = tk.Frame(self.canvas_maestrias, bg=COR_FUNDO)
        janela = self.canvas_maestrias.create_window(
            (0, 0), window=self.frame_maestrias, anchor="nw",
        )

        self.canvas_maestrias.bind(
            "<Configure>",
            lambda e: self.canvas_maestrias.itemconfigure(janela, width=e.width),
        )
        self.frame_maestrias.bind(
            "<Configure>",
            lambda e: self.canvas_maestrias.configure(
                scrollregion=self.canvas_maestrias.bbox("all")
            ),
        )
        self.canvas_maestrias.bind("<Enter>", lambda e: self._ligar_scroll_maestrias())
        self.canvas_maestrias.bind("<Leave>", lambda e: self._desligar_scroll_maestrias())

        self._montar_secao_maestria(
            "ELEMENTAIS", "elementais", MAESTRIAS_ELEMENTAIS, pady_topo=(10, 6),
        )
        self._montar_secao_maestria(
            "PRIMORDIAIS", "primordiais", MAESTRIAS_PRIMORDIAIS, pady_topo=(20, 6),
        )

    def _ligar_scroll_maestrias(self):
        self.canvas_maestrias.bind_all("<MouseWheel>", self._scroll_maestrias)

    def _desligar_scroll_maestrias(self):
        self.canvas_maestrias.unbind_all("<MouseWheel>")

    def _scroll_maestrias(self, event):
        self.canvas_maestrias.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _montar_secao_maestria(self, titulo, grupo, nomes, pady_topo=(10, 6)):
        tk.Label(
            self.frame_maestrias, text=titulo, font=("Segoe UI", 12, "bold"),
            bg=COR_FUNDO, fg=COR_TEXTO, anchor="w",
        ).pack(fill="x", padx=10, pady=pady_topo)

        grade = tk.Frame(self.frame_maestrias, bg=COR_FUNDO)
        grade.pack(fill="x", padx=10)

        for c in range(len(nomes)):
            grade.grid_columnconfigure(c, weight=1, uniform=f"mae_{grupo}")

        for idx, nome in enumerate(nomes):
            self._criar_celula_maestria(grade, grupo, nome).grid(
                row=0, column=idx, padx=6, pady=4, sticky="nsew",
            )

    def _criar_celula_maestria(self, parent, grupo, nome):
        celula = tk.Frame(parent, bg=COR_FUNDO_PAINEL,
                          highlightthickness=1, highlightbackground=COR_BORDA)

        tk.Label(
            celula, text=nome, font=("Segoe UI", 11, "bold"),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO,
        ).pack(pady=(14, 6))

        controle = tk.Frame(celula, bg=COR_FUNDO_PAINEL)
        controle.pack(pady=(0, 16))

        menos = tk.Label(
            controle, text="−", font=("Segoe UI", 14, "bold"),
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO, width=2, cursor="hand2",
        )
        menos.pack(side="left", padx=(0, 10))
        menos.bind("<Button-1>", lambda e, g=grupo, n=nome: self._ajustar_maestria(g, n, -1))

        valor = tk.Label(
            controle, text="0", font=("Segoe UI", 20),
            bg=COR_FUNDO_PAINEL, fg=COR_TEXTO, width=3,
        )
        valor.pack(side="left")
        self.labels_maestrias[grupo][nome] = valor

        mais = tk.Label(
            controle, text="+", font=("Segoe UI", 14, "bold"),
            bg=COR_FUNDO_CAMPO, fg=COR_TEXTO, width=2, cursor="hand2",
        )
        mais.pack(side="left", padx=(10, 0))
        mais.bind("<Button-1>", lambda e, g=grupo, n=nome: self._ajustar_maestria(g, n, 1))

        return celula

    def _ajustar_maestria(self, grupo, nome, delta):
        novo = self.maestrias[grupo][nome] + delta
        novo = max(0, min(MAESTRIA_MAX, novo))
        self.maestrias[grupo][nome] = novo
        self.labels_maestrias[grupo][nome].configure(text=str(novo))

    # ----- rodape -----

    def _montar_rodape(self, parent):
        rodape = tk.Frame(parent, bg=COR_FUNDO)
        rodape.pack(fill="x", pady=(12, 0))

        cancelar = tk.Label(
            rodape, text="Cancelar", font=FONTE_BOTAO,
            bg=COR_FUNDO, fg=COR_TEXTO_SUAVE,
            cursor="hand2", padx=14, pady=6,
        )
        cancelar.pack(side="right", padx=(0, 8))
        cancelar.bind("<Button-1>", lambda e: self.destroy())
        cancelar.bind("<Enter>", lambda e: cancelar.configure(fg=COR_TEXTO))
        cancelar.bind("<Leave>", lambda e: cancelar.configure(fg=COR_TEXTO_SUAVE))

        salvar = tk.Label(
            rodape, text="Salvar", font=FONTE_BOTAO,
            bg=COR_DESTAQUE, fg=COR_TEXTO,
            cursor="hand2", padx=20, pady=8,
        )
        salvar.pack(side="right")
        salvar.bind("<Button-1>", lambda e: self._salvar())
        salvar.bind("<Enter>", lambda e: salvar.configure(bg=COR_DESTAQUE_HOVER))
        salvar.bind("<Leave>", lambda e: salvar.configure(bg=COR_DESTAQUE))

    def _salvar(self):
        nome = self.campo_nome.get().strip()
        if not nome:
            messagebox.showwarning("Atencao", "O nome do personagem e obrigatorio.", parent=self)
            return

        for chave in ("vida", "energia", "sanidade"):
            try:
                self._sincronizar_barra(chave)
            except Exception:
                pass

        if self.imagem_origem:
            try:
                imagem_path = copiar_imagem(self.imagem_origem)
            except Exception as erro:
                messagebox.showerror("Erro", f"Nao foi possivel salvar a imagem:\n{erro}", parent=self)
                return
        else:
            imagem_path = self.imagem_path_salvo

        descricao = self.text_descricao.get("1.0", "end").strip()
        armamentos = [dict(a) for a in self.armamentos]
        itens = [dict(i) for i in self.itens]
        habilidades = [dict(h) for h in self.habilidades]
        maestrias = {
            "elementais": dict(self.maestrias["elementais"]),
            "primordiais": dict(self.maestrias["primordiais"]),
        }

        if self.modo_edicao:
            personagem = dict(self.existente)
            personagem.update({
                "nome": nome,
                "idade": self.campo_idade.get().strip(),
                "nascimento": self._ler_data(self.campos_nasc),
                "cristalizacao": self._ler_data(self.campos_crist),
                "nivel_lc": self.nivel_lc,
                "vida_atual": self.vida_atual,
                "vida_maxima": self.vida_maxima,
                "energia_atual": self.energia_atual,
                "energia_maxima": self.energia_maxima,
                "sanidade": self.sanidade,
                "atributos": dict(self.atributos),
                "descricao": descricao,
                "armamentos": armamentos,
                "itens": itens,
                "habilidades": habilidades,
                "maestrias": maestrias,
                "imagem": imagem_path,
            })
            try:
                if not atualizar_personagem(personagem):
                    messagebox.showerror("Erro", "Personagem original nao encontrado.", parent=self)
                    return
            except Exception as erro:
                messagebox.showerror("Erro", f"Nao foi possivel atualizar o personagem:\n{erro}", parent=self)
                return
            messagebox.showinfo("Salvo", f"Personagem '{nome}' atualizado.", parent=self)
            self.destroy()
            return

        personagem = {
            "id": uuid.uuid4().hex,
            "criado_por": self.criado_por,
            "criado_em": datetime.now().strftime("%d/%m/%y"),
            "nome": nome,
            "idade": self.campo_idade.get().strip(),
            "nascimento": self._ler_data(self.campos_nasc),
            "cristalizacao": self._ler_data(self.campos_crist),
            "nivel_lc": self.nivel_lc,
            "vida_atual": self.vida_atual,
            "vida_maxima": self.vida_maxima,
            "energia_atual": self.energia_atual,
            "energia_maxima": self.energia_maxima,
            "sanidade": self.sanidade,
            "atributos": dict(self.atributos),
            "descricao": descricao,
            "armamentos": armamentos,
            "itens": itens,
            "habilidades": habilidades,
            "maestrias": maestrias,
            "imagem": imagem_path,
        }

        try:
            salvar_personagem(personagem)
        except Exception as erro:
            messagebox.showerror("Erro", f"Nao foi possivel salvar o personagem:\n{erro}", parent=self)
            return

        messagebox.showinfo("Salvo", f"Personagem '{nome}' criado.", parent=self)
        self.destroy()

    def _preencher_com_existente(self):
        p = self.existente or {}

        self.campo_nome.insert(0, p.get("nome", ""))
        self.campo_idade.insert(0, p.get("idade", ""))
        self._preencher_data(self.campos_nasc, p.get("nascimento", ""))
        self._preencher_data(self.campos_crist, p.get("cristalizacao", ""))

        nivel = p.get("nivel_lc")
        if isinstance(nivel, int) and 0 <= nivel < len(self.botoes_lc):
            self.nivel_lc = nivel
            for i, botao in enumerate(self.botoes_lc):
                if i == nivel:
                    botao.configure(bg=COR_DESTAQUE, fg=COR_TEXTO)
                else:
                    botao.configure(bg=COR_FUNDO_CAMPO, fg=COR_TEXTO)

        atributos_salvos = p.get("atributos") or {}
        for nome in ATRIBUTOS_NOMES:
            valor = int(atributos_salvos.get(nome, 0) or 0)
            self.atributos[nome] = max(0, valor)
            if nome in self.labels_atributos:
                self.labels_atributos[nome].configure(text=str(self.atributos[nome]))

        self.vida_maxima = int(p.get("vida_maxima",
                                     calcular_vida_maxima(self.nivel_lc, self.atributos["VITALIDADE"])))
        self.vida_atual = int(p.get("vida_atual", self.vida_maxima))
        self.energia_maxima = int(p.get("energia_maxima",
                                        calcular_energia_maxima(self.nivel_lc, self.atributos["PRESENCA"])))
        self.energia_atual = int(p.get("energia_atual", self.energia_maxima))
        self.sanidade = int(p.get("sanidade", SANIDADE_INICIAL))

        for chave in ("vida", "energia", "sanidade"):
            self._atualizar_entries(chave)
            self._desenhar_barra(chave)

        descricao = p.get("descricao", "") or ""
        if descricao:
            self.text_descricao.insert("1.0", descricao)

        self.armamentos = []
        for arma in (p.get("armamentos") or []):
            self.armamentos.append({
                "id": arma.get("id") or uuid.uuid4().hex,
                "nome": arma.get("nome", ""),
                "tipo": arma.get("tipo", TIPO_ARMA_PADRAO),
                "dano": arma.get("dano", ""),
                "municao_atual": int(arma.get("municao_atual", 0) or 0),
                "municao_maxima": int(arma.get("municao_maxima", 0) or 0),
                "descricao": arma.get("descricao", ""),
            })
        self.itens = []
        for item in (p.get("itens") or []):
            self.itens.append({
                "id": item.get("id") or uuid.uuid4().hex,
                "tipo": item.get("tipo", TIPO_ITEM_PADRAO),
                "nome": item.get("nome", ""),
                "quantidade": int(item.get("quantidade", 1) or 0),
                "descricao": item.get("descricao", ""),
            })
        self._renderizar_inventario()

        self.habilidades = []
        for hab in (p.get("habilidades") or []):
            self.habilidades.append({
                "id": hab.get("id") or uuid.uuid4().hex,
                "nome": hab.get("nome", ""),
                "descricao": hab.get("descricao", ""),
            })
        self._renderizar_habilidades()

        maestrias_salvas = p.get("maestrias") or {}
        for grupo, nomes in (
            ("elementais", MAESTRIAS_ELEMENTAIS),
            ("primordiais", MAESTRIAS_PRIMORDIAIS),
        ):
            grupo_salvo = maestrias_salvas.get(grupo) or {}
            for nome in nomes:
                valor = int(grupo_salvo.get(nome, 0) or 0)
                valor = max(0, min(MAESTRIA_MAX, valor))
                self.maestrias[grupo][nome] = valor
                if nome in self.labels_maestrias[grupo]:
                    self.labels_maestrias[grupo][nome].configure(text=str(valor))

        imagem_path = p.get("imagem", "")
        self.imagem_path_salvo = imagem_path
        if imagem_path:
            caminho_abs = caminho_imagem(imagem_path)
            if caminho_abs:
                try:
                    img = Image.open(caminho_abs)
                    img.thumbnail((self.TAMANHO_IMAGEM, self.TAMANHO_IMAGEM), Image.LANCZOS)
                    self.imagem_tk = ImageTk.PhotoImage(img)
                    self.label_imagem.configure(image=self.imagem_tk, text="")
                except Exception:
                    pass

    def _preencher_data(self, partes, valor):
        if not valor:
            return
        pedacos = valor.split("/")
        for ent, ped in zip(partes, pedacos):
            ped = (ped or "").strip()
            if not ped or ped == "--":
                continue
            ent.delete(0, tk.END)
            ent.insert(0, ped)
            ent.configure(fg=COR_TEXTO)


if __name__ == "__main__":
    TelaLogin().mainloop()
