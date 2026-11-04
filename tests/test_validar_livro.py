import app


def test_dados_vazios():
    assert app.validar_livro(None) == "Dados inválidos"


def test_titulo_nao_informado():
    dados = {"autor": "Machado de Assis", "ano": 1899}
    assert app.validar_livro(dados) == "Informe o título"


def test_titulo_muito_curto():
    dados = {"titulo": "AB", "autor": "Machado", "ano": 1899}
    assert app.validar_livro(dados) == "Título muito curto"


def test_autor_nao_informado():
    dados = {"titulo": "Dom Casmurro", "ano": 1899}
    assert app.validar_livro(dados) == "Informe o autor"


def test_ano_nao_informado():
    dados = {"titulo": "Dom Casmurro", "autor": "Machado"}
    assert app.validar_livro(dados) == "Informe o ano"


def test_ano_com_valor_invalido():
    dados = {"titulo": "Dom Casmurro", "autor": "Machado", "ano": "abc"}
    assert app.validar_livro(dados) == "Ano inválido"


def test_ano_no_limite_minimo():
    dados = {"titulo": "Dom Casmurro", "autor": "Machado", "ano": 1000}
    assert app.validar_livro(dados) == "Ano inválido"


def test_ano_futuro():
    dados = {
        "titulo": "Dom Casmurro",
        "autor": "Machado",
        "ano": app.date.today().year + 1
    }
    assert app.validar_livro(dados) == "Ano inválido"


def test_livro_valido():
    dados = {
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1899
    }
    assert app.validar_livro(dados) is None

def test_titulo_no_limite_minimo():
    dados = {
        "titulo": "ABC",
        "autor": "Machado",
        "ano": 1899
    }
    assert app.validar_livro(dados) is None

def test_ano_acima_do_limite_minimo():
    dados = {
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 1001
    }
    assert app.validar_livro(dados) is None

def test_ano_atual():
    dados = {
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": app.date.today().year
    }
    assert app.validar_livro(dados) is None

def test_ano_abaixo_do_limite_minimo():
    dados = {
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "ano": 999
    }
    assert app.validar_livro(dados) == "Ano inválido"