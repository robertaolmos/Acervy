from datetime import date, timedelta
import app


def test_devolucao_no_prazo():
    data_prevista = date(2026, 10, 20)
    data_devolucao = date(2026, 10, 20)

    assert app.calcular_multa(data_devolucao, data_prevista) == 0


def test_devolucao_antes_do_prazo():
    data_prevista = date(2026, 10, 20)
    data_devolucao = date(2026, 10, 18)

    assert app.calcular_multa(data_devolucao, data_prevista) == 0


def test_devolucao_com_um_dia_de_atraso():
    data_prevista = date(2026, 10, 20)
    data_devolucao = date(2026, 10, 21)

    assert app.calcular_multa(data_devolucao, data_prevista) == 2.5


def test_devolucao_com_varios_dias_de_atraso():
    data_prevista = date(2026, 10, 20)
    data_devolucao = date(2026, 10, 24)

    assert app.calcular_multa(data_devolucao, data_prevista) == 10.0

def test_multa_utiliza_valor_por_dia():
    data_prevista = date(2026, 10, 20)
    data_devolucao = date(2026, 10, 22)

    assert app.calcular_multa(data_devolucao, data_prevista) == (
        2 * app.MULTA_POR_DIA
    )

def test_devolucao_muito_antes_do_prazo():
    data_prevista = date(2026, 10, 20)
    data_devolucao = date(2026, 10, 10)

    assert app.calcular_multa(data_devolucao, data_prevista) == 0