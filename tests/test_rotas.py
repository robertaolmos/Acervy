import pytest
import app


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    banco_teste = tmp_path / "teste.db"
    monkeypatch.setattr(app, "BANCO_DADOS", str(banco_teste))

    app.inicializar_banco()

    with app.app.test_client() as cliente:
        yield cliente


def test_cadastrar_livro_com_dados_validos(cliente):
    resposta = cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    assert resposta.status_code == 200
    assert resposta.json["ok"] == 1


def test_cadastrar_livro_sem_titulo(cliente):
    resposta = cliente.post("/api/livros", json={
        "autor": "Machado de Assis",
        "ano": 1899
    })

    assert resposta.status_code == 400
    assert resposta.json["msg"] == "Informe o título"


def test_cadastrar_livro_com_ano_invalido(cliente):
    resposta = cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": "abc"
    })

    assert resposta.status_code == 400
    assert resposta.json["msg"] == "Ano inválido"

def test_listar_todos_os_livros(cliente):
    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    resposta = cliente.get("/api/lista/todos")

    assert resposta.status_code == 200
    assert len(resposta.json) == 1
    assert resposta.json[0]["titulo"] == "Dom Casmurro"


def test_listar_livros_disponiveis(cliente):
    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    resposta = cliente.get("/api/lista/disp")

    assert resposta.status_code == 200
    assert len(resposta.json) == 1
    assert resposta.json[0]["status"] == "Disponível"


def test_tipo_de_lista_invalido(cliente):
    resposta = cliente.get("/api/lista/invalido")

    assert resposta.status_code == 400
    assert resposta.json["msg"] == "Tipo de lista inválido"


def test_emprestar_livro_com_usuario_vazio(cliente):
    resposta = cliente.post("/api/emprestar", json={
        "id": 1,
        "user": ""
    })

    assert resposta.status_code == 400
    assert resposta.json["msg"] == "Informe o nome do usuário"


def test_emprestar_livro_inexistente(cliente):
    resposta = cliente.post("/api/emprestar", json={
        "id": 999,
        "user": "Maria"
    })

    assert resposta.status_code == 404
    assert resposta.json["msg"] == "Livro não encontrado"


def test_emprestar_e_devolver_livro(cliente):
    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    emprestimo = cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "Maria"
    })

    assert emprestimo.status_code == 200
    assert emprestimo.json["ok"] == 1

    devolucao = cliente.get("/api/lista/pend")
    assert len(devolucao.json) == 1

    emprestimo_id = devolucao.json[0]["id"]

    resposta = cliente.post("/api/devolver", json={
        "id": emprestimo_id
    })

    assert resposta.status_code == 200
    assert resposta.json["ok"] == 1

    devolvidos = cliente.get("/api/lista/dev")
    assert len(devolvidos.json) == 1
    assert devolvidos.json[0]["data_devolucao"] is not None

def test_emprestar_livro_ja_emprestado(cliente):
    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "Maria"
    })

    resposta = cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "João"
    })

    assert resposta.status_code == 400
    assert resposta.json["msg"] == "Livro já emprestado"


def test_limite_de_emprestimos_por_usuario(cliente):
    for i in range(4):
        cliente.post("/api/livros", json={
            "titulo": f"Livro {i + 1}",
            "autor": "Autor",
            "ano": 2000
        })

    for i in range(3):
        resposta = cliente.post("/api/emprestar", json={
            "id": i + 1,
            "user": "Maria"
        })
        assert resposta.status_code == 200

    resposta = cliente.post("/api/emprestar", json={
        "id": 4,
        "user": "Maria"
    })

    assert resposta.status_code == 400
    assert resposta.json["msg"] == "Limite de 3 livros por leitor"

def test_devolver_emprestimo_inexistente(cliente):
    resposta = cliente.post("/api/devolver", json={
        "id": 999
    })

    assert resposta.status_code == 400
    assert resposta.json["msg"] == "Empréstimo não encontrado ou já devolvido"


def test_devolver_emprestimo_ja_devolvido(cliente):
    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    emprestimo = cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "Maria"
    })

    lista = cliente.get("/api/lista/pend")
    emprestimo_id = lista.json[0]["id"]

    primeira_devolucao = cliente.post("/api/devolver", json={
        "id": emprestimo_id
    })

    segunda_devolucao = cliente.post("/api/devolver", json={
        "id": emprestimo_id
    })

    assert primeira_devolucao.status_code == 200
    assert segunda_devolucao.status_code == 400
    assert segunda_devolucao.json["msg"] == "Empréstimo não encontrado ou já devolvido"

def test_listar_emprestimo_atrasado(cliente, monkeypatch):
    from datetime import date, timedelta

    hoje = date.today()
    data_atrasada = hoje - timedelta(days=1)

    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "Maria"
    })

    emprestimo = cliente.get("/api/lista/pend")
    emprestimo_id = emprestimo.json[0]["id"]

    import sqlite3
    conexao = sqlite3.connect(app.BANCO_DADOS)
    conexao.execute(
        "UPDATE emprestimos SET data_prevista = ? WHERE id = ?",
        (str(data_atrasada), emprestimo_id)
    )
    conexao.commit()
    conexao.close()

    resposta = cliente.get("/api/lista/pend")

    assert resposta.status_code == 200
    assert len(resposta.json) == 1
    assert resposta.json[0]["atrasado"] is True

def test_devolucao_registra_multa(cliente):
    from datetime import date, timedelta
    import sqlite3

    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "Maria"
    })

    emprestimos = cliente.get("/api/lista/pend")
    emprestimo_id = emprestimos.json[0]["id"]

    data_atrasada = date.today() - timedelta(days=2)

    conexao = sqlite3.connect(app.BANCO_DADOS)
    conexao.execute(
        "UPDATE emprestimos SET data_prevista = ? WHERE id = ?",
        (str(data_atrasada), emprestimo_id)
    )
    conexao.commit()
    conexao.close()

    resposta = cliente.post("/api/devolver", json={
        "id": emprestimo_id
    })

    assert resposta.status_code == 200

    conexao = sqlite3.connect(app.BANCO_DADOS)
    resultado = conexao.execute(
        "SELECT multa FROM emprestimos WHERE id = ?",
        (emprestimo_id,)
    ).fetchone()
    conexao.close()

    assert resultado[0] == 5.0

def test_livro_fica_emprestado_apos_emprestimo(cliente):
    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "Maria"
    })

    import sqlite3
    conexao = sqlite3.connect(app.BANCO_DADOS)
    resultado = conexao.execute(
        "SELECT status FROM livros WHERE id = 1"
    ).fetchone()
    conexao.close()

    assert resultado[0] == app.LIVRO_EMPRESTADO


def test_livro_volta_a_ficar_disponivel_apos_devolucao(cliente):
    cliente.post("/api/livros", json={
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    })

    cliente.post("/api/emprestar", json={
        "id": 1,
        "user": "Maria"
    })

    emprestimos = cliente.get("/api/lista/pend")
    emprestimo_id = emprestimos.json[0]["id"]

    cliente.post("/api/devolver", json={
        "id": emprestimo_id
    })

    import sqlite3
    conexao = sqlite3.connect(app.BANCO_DADOS)
    resultado = conexao.execute(
        "SELECT status FROM livros WHERE id = 1"
    ).fetchone()
    conexao.close()

    assert resultado[0] == app.LIVRO_DISPONIVEL