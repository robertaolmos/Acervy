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


def resposta_erro(mensagem, codigo=400):
    return jsonify({
        "ok": 0,
        "msg": mensagem
    }), codigo


def validar_livro(dados):
    if not dados:
        return "Dados inválidos"

    if not dados.get("titulo"):
        return "Informe o título"

    if len(dados["titulo"]) < TAMANHO_MINIMO_TITULO:
        return "Título muito curto"

    if not dados.get("autor"):
        return "Informe o autor"

    if not dados.get("ano"):
        return "Informe o ano"

    try:
        ano = int(dados["ano"])
    except (TypeError, ValueError):
        return "Ano inválido"

    if ano <= ANO_MINIMO_LIVRO or ano > date.today().year:
        return "Ano inválido"

    return None


def calcular_multa(data_devolucao, data_prevista):
    dias_atrasados = (data_devolucao - data_prevista).days

    if dias_atrasados <= 0:
        return 0

    return dias_atrasados * MULTA_POR_DIA


@app.route("/")
def pagina_inicial():
    return send_from_directory("static", "index.html")


@app.route("/<path:arquivo>")
def arquivos_estaticos(arquivo):
    return send_from_directory("static", arquivo)


@app.route("/api/livros", methods=["POST"])
def adicionar_livro():
    dados = request.get_json(silent=True)
    erro = validar_livro(dados)

    if erro:
        return resposta_erro(erro)

    titulo = dados["titulo"].strip()
    autor = dados["autor"].strip()
    ano = int(dados["ano"])

    conexao = conectar_banco()

    conexao.execute(
        """
        INSERT INTO livros (titulo, autor, status, ano)
        VALUES (?, ?, ?, ?)
        """,
        (titulo, autor, LIVRO_DISPONIVEL, ano)
    )

    conexao.commit()
    conexao.close()

    return jsonify({
        "ok": 1,
        "msg": "Livro cadastrado!"
    })


@app.route("/api/lista/<tipo_lista>")
def listar_itens(tipo_lista):
    conexao = conectar_banco()

    if tipo_lista == "todos" or tipo_lista == "disp":
        consulta = "SELECT * FROM livros"
        parametros = ()

        if tipo_lista == "disp":
            consulta += " WHERE status = ?"
            parametros = (LIVRO_DISPONIVEL,)

        livros = conexao.execute(
            consulta,
            parametros
        ).fetchall()

        resultado = []

        for livro in livros:
            status = (
                "Disponível"
                if livro["status"] == LIVRO_DISPONIVEL
                else "Emprestado"
            )

            resultado.append({
                "id": livro["id"],
                "titulo": livro["titulo"],
                "autor": livro["autor"],
                "ano": livro["ano"],
                "status": status
            })

    elif tipo_lista == "pend" or tipo_lista == "dev":
        consulta = """
            SELECT
                emprestimos.*,
                livros.titulo
            FROM emprestimos
            JOIN livros
                ON livros.id = emprestimos.livro_id
        """

        if tipo_lista == "pend":
            consulta += " WHERE emprestimos.data_devolucao IS NULL"
        else:
            consulta += " WHERE emprestimos.data_devolucao IS NOT NULL"

        emprestimos = conexao.execute(consulta).fetchall()
        resultado = []

        for emprestimo in emprestimos:
            esta_atrasado = (
                emprestimo["data_devolucao"] is None
                and str(date.today()) > emprestimo["data_prevista"]
            )

            resultado.append({
                "id": emprestimo["id"],
                "titulo": emprestimo["titulo"],
                "usuario": emprestimo["usuario"],
                "data_emprestimo": emprestimo["data_emprestimo"],
                "data_prevista": emprestimo["data_prevista"],
                "data_devolucao": emprestimo["data_devolucao"],
                "multa": emprestimo["multa"],
                "atrasado": esta_atrasado
            })

    else:
        conexao.close()
        return resposta_erro("Tipo de lista inválido")

    conexao.close()

    return jsonify(resultado)


@app.route("/api/emprestar", methods=["POST"])
def realizar_emprestimo():
    dados = request.get_json(silent=True)

    if not dados:
        return resposta_erro("Dados inválidos")

    livro_id = dados.get("id")
    usuario = dados.get("user", "").strip()

    if not usuario:
        return resposta_erro("Informe o nome do usuário")

    conexao = conectar_banco()

    livro = conexao.execute(
        """
        SELECT *
        FROM livros
        WHERE id = ?
        """,
        (livro_id,)
    ).fetchone()

    if not livro:
        conexao.close()
        return resposta_erro("Livro não encontrado", 404)

    if livro["status"] != LIVRO_DISPONIVEL:
        conexao.close()
        return resposta_erro("Livro já emprestado")

    quantidade_emprestimos = conexao.execute(
        """
        SELECT COUNT(*)
        FROM emprestimos
        WHERE usuario = ?
          AND data_devolucao IS NULL
        """,
        (usuario,)
    ).fetchone()[0]

    if quantidade_emprestimos >= LIMITE_LIVROS_POR_USUARIO:
        conexao.close()
        return resposta_erro(
            "Limite de 3 livros por leitor"
        )

    data_emprestimo = date.today()
    data_prevista = (
        data_emprestimo
        + timedelta(days=PRAZO_EMPRESTIMO_DIAS)
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
        (LIVRO_EMPRESTADO, livro_id)
    )

    conexao.commit()
    conexao.close()

    return jsonify({
        "ok": 1,
        "msg": f"Emprestado! Devolver até {data_prevista}"
    })


@app.route("/api/devolver", methods=["POST"])
def realizar_devolucao():
    dados = request.get_json(silent=True)

    if not dados:
        return resposta_erro("Dados inválidos")

    emprestimo_id = dados.get("id")

    if not emprestimo_id:
        return resposta_erro("Informe o empréstimo")

    conexao = conectar_banco()

    emprestimo = conexao.execute(
        """
        SELECT *
        FROM emprestimos
        WHERE id = ?
        """,
        (emprestimo_id,)
    ).fetchone()

    if not emprestimo or emprestimo["data_devolucao"] is not None:
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
        SET data_devolucao = ?, multa = ?
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
        (LIVRO_DISPONIVEL, emprestimo["livro_id"])
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
