from datetime import date, timedelta
import sqlite3

from flask import Flask, jsonify, request, send_from_directory


app = Flask(__name__)

BANCO_DADOS = "lib.db"

TAMANHO_MINIMO_TITULO = 3
ANO_MINIMO_LIVRO = 1000
LIMITE_LIVROS_POR_USUARIO = 3
PRAZO_EMPRESTIMO_DIAS = 14
MULTA_POR_DIA = 2.5

LIVRO_DISPONIVEL = 0
LIVRO_EMPRESTADO = 1


def conectar_banco():
    conexao = sqlite3.connect(BANCO_DADOS)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco():
    conexao = conectar_banco()

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            status INTEGER NOT NULL,
            ano INTEGER NOT NULL
        )
        """
    )

    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            livro_id INTEGER NOT NULL,
            usuario TEXT NOT NULL,
            data_emprestimo TEXT NOT NULL,
            data_prevista TEXT NOT NULL,
            data_devolucao TEXT,
            multa REAL DEFAULT 0,
            FOREIGN KEY (livro_id) REFERENCES livros (id)
        )
        """
    )

    conexao.commit()
    conexao.close()


def obter_dados_requisicao():
    return request.get_json(silent=True)


def resposta_erro(mensagem, codigo=400):
    return jsonify({
        "ok": 0,
        "msg": mensagem
    }), codigo


def validar_livro(dados):
    if not dados:
        return "Dados inválidos"

    titulo = dados.get("titulo", "").strip()
    autor = dados.get("autor", "").strip()
    ano = dados.get("ano")

    if not titulo:
        return "Informe o título"

    if len(titulo) < TAMANHO_MINIMO_TITULO:
        return "Título muito curto"

    if not autor:
        return "Informe o autor"

    if not ano:
        return "Informe o ano"

    try:
        ano = int(ano)
    except (TypeError, ValueError):
        return "Ano inválido"

    ano_atual = date.today().year

    if ano <= ANO_MINIMO_LIVRO or ano > ano_atual:
        return "Ano inválido"

    return None


def salvar_livro(dados):
    conexao = conectar_banco()

    titulo = dados["titulo"].strip()
    autor = dados["autor"].strip()
    ano = int(dados["ano"])

    conexao.execute(
        """
        INSERT INTO livros (titulo, autor, status, ano)
        VALUES (?, ?, ?, ?)
        """,
        (
            titulo,
            autor,
            LIVRO_DISPONIVEL,
            ano
        )
    )

    conexao.commit()
    conexao.close()


def buscar_livro(conexao, livro_id):
    return conexao.execute(
        """
        SELECT *
        FROM livros
        WHERE id = ?
        """,
        (livro_id,)
    ).fetchone()


def buscar_emprestimo(conexao, emprestimo_id):
    return conexao.execute(
        """
        SELECT *
        FROM emprestimos
        WHERE id = ?
        """,
        (emprestimo_id,)
    ).fetchone()


def contar_emprestimos_ativos(conexao, usuario):
    resultado = conexao.execute(
        """
        SELECT COUNT(*)
        FROM emprestimos
        WHERE usuario = ?
          AND data_devolucao IS NULL
        """,
        (usuario,)
    )

    return resultado.fetchone()[0]


def calcular_data_prevista(data_emprestimo):
    return data_emprestimo + timedelta(days=PRAZO_EMPRESTIMO_DIAS)


def calcular_multa(data_devolucao, data_prevista):
    dias_atrasados = (data_devolucao - data_prevista).days

    if dias_atrasados <= 0:
        return 0

    return dias_atrasados * MULTA_POR_DIA


def converter_livro_para_json(livro):
    if livro["status"] == LIVRO_DISPONIVEL:
        status = "Disponível"
    else:
        status = "Emprestado"

    return {
        "id": livro["id"],
        "titulo": livro["titulo"],
        "autor": livro["autor"],
        "ano": livro["ano"],
        "status": status
    }


def converter_emprestimo_para_json(emprestimo):
    data_atual = date.today()

    esta_atrasado = (
        emprestimo["data_devolucao"] is None
        and str(data_atual) > emprestimo["data_prevista"]
    )

    return {
        "id": emprestimo["id"],
        "titulo": emprestimo["titulo"],
        "usuario": emprestimo["usuario"],
        "data_emprestimo": emprestimo["data_emprestimo"],
        "data_prevista": emprestimo["data_prevista"],
        "data_devolucao": emprestimo["data_devolucao"],
        "multa": emprestimo["multa"],
        "atrasado": esta_atrasado
    }


def listar_livros(conexao, somente_disponiveis=False):
    consulta = """
        SELECT *
        FROM livros
    """

    parametros = ()

    if somente_disponiveis:
        consulta += " WHERE status = ?"
        parametros = (LIVRO_DISPONIVEL,)

    return conexao.execute(
        consulta,
        parametros
    ).fetchall()


def listar_emprestimos(conexao, somente_pendentes):
    consulta = """
        SELECT
            emprestimos.*,
            livros.titulo
        FROM emprestimos
        JOIN livros
            ON livros.id = emprestimos.livro_id
    """

    if somente_pendentes:
        consulta += " WHERE emprestimos.data_devolucao IS NULL"
    else:
        consulta += " WHERE emprestimos.data_devolucao IS NOT NULL"

    return conexao.execute(consulta).fetchall()


@app.route("/")
def pagina_inicial():
    return send_from_directory("static", "index.html")


@app.route("/<path:arquivo>")
def arquivos_estaticos(arquivo):
    return send_from_directory("static", arquivo)


@app.route("/api/livros", methods=["POST"])
def adicionar_livro():
    dados = obter_dados_requisicao()
    erro = validar_livro(dados)

    if erro:
        return resposta_erro(erro)

    salvar_livro(dados)

    return jsonify({
        "ok": 1,
        "msg": "Livro cadastrado!"
    })


@app.route("/api/lista/<tipo_lista>")
def listar_itens(tipo_lista):
    conexao = conectar_banco()

    if tipo_lista == "todos":
        livros = listar_livros(conexao)

        resultado = [
            converter_livro_para_json(livro)
            for livro in livros
        ]

    elif tipo_lista == "disp":
        livros = listar_livros(
            conexao,
            somente_disponiveis=True
        )

        resultado = [
            converter_livro_para_json(livro)
            for livro in livros
        ]

    elif tipo_lista == "pend":
        emprestimos = listar_emprestimos(
            conexao,
            somente_pendentes=True
        )

        resultado = [
            converter_emprestimo_para_json(emprestimo)
            for emprestimo in emprestimos
        ]

    elif tipo_lista == "dev":
        emprestimos = listar_emprestimos(
            conexao,
            somente_pendentes=False
        )

        resultado = [
            converter_emprestimo_para_json(emprestimo)
            for emprestimo in emprestimos
        ]

    else:
        conexao.close()
        return resposta_erro("Tipo de lista inválido")

    conexao.close()

    return jsonify(resultado)


@app.route("/api/emprestar", methods=["POST"])
def realizar_emprestimo():
    dados = obter_dados_requisicao()

    if not dados:
        return resposta_erro("Dados inválidos")

    livro_id = dados.get("id")
    usuario = dados.get("user", "").strip()

    if not usuario:
        return resposta_erro("Informe o nome do usuário")

    conexao = conectar_banco()
    livro = buscar_livro(conexao, livro_id)

    if not livro:
        conexao.close()

        return resposta_erro(
            "Livro não encontrado",
            404
        )

    if livro["status"] != LIVRO_DISPONIVEL:
        conexao.close()

        return resposta_erro(
            "Livro já emprestado"
        )

    quantidade_emprestimos = contar_emprestimos_ativos(
        conexao,
        usuario
    )

    if quantidade_emprestimos >= LIMITE_LIVROS_POR_USUARIO:
        conexao.close()

        return resposta_erro(
            "Limite de 3 livros por leitor"
        )

    data_emprestimo = date.today()
    data_prevista = calcular_data_prevista(
        data_emprestimo
    )

    conexao.execute(
        """
        INSERT INTO emprestimos (
            livro_id,
            usuario,
            data_emprestimo,
            data_prevista
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            livro_id,
            usuario,
            str(data_emprestimo),
            str(data_prevista)
        )
    )

    conexao.execute(
        """
        UPDATE livros
        SET status = ?
        WHERE id = ?
        """,
        (
            LIVRO_EMPRESTADO,
            livro_id
        )
    )

    conexao.commit()
    conexao.close()

    return jsonify({
        "ok": 1,
        "msg": f"Emprestado! Devolver até {data_prevista}"
    })


@app.route("/api/devolver", methods=["POST"])
def realizar_devolucao():
    dados = obter_dados_requisicao()

    if not dados:
        return resposta_erro("Dados inválidos")

    emprestimo_id = dados.get("id")

    if not emprestimo_id:
        return resposta_erro(
            "Informe o empréstimo"
        )

    conexao = conectar_banco()

    emprestimo = buscar_emprestimo(
        conexao,
        emprestimo_id
    )

    if not emprestimo:
        conexao.close()

        return resposta_erro(
            "Empréstimo não encontrado ou já devolvido"
        )

    if emprestimo["data_devolucao"] is not None:
        conexao.close()

        return resposta_erro(
            "Empréstimo não encontrado ou já devolvido"
        )

    data_devolucao = date.today()

    data_prevista = date.fromisoformat(
        emprestimo["data_prevista"]
    )

    multa = calcular_multa(
        data_devolucao,
        data_prevista
    )

    conexao.execute(
        """
        UPDATE emprestimos
        SET
            data_devolucao = ?,
            multa = ?
        WHERE id = ?
        """,
        (
            str(data_devolucao),
            multa,
            emprestimo_id
        )
    )

    conexao.execute(
        """
        UPDATE livros
        SET status = ?
        WHERE id = ?
        """,
        (
            LIVRO_DISPONIVEL,
            emprestimo["livro_id"]
        )
    )

    conexao.commit()
    conexao.close()

    mensagem = "Livro devolvido!"

    if multa > 0:
        mensagem += f" Multa: R$ {multa:.2f}"

    return jsonify({
        "ok": 1,
        "msg": mensagem
    })


if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True)
