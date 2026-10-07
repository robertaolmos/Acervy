const API = "/api";
const ANO_MINIMO_LIVRO = 1000;

let abaAtual = "todos";


function buscar(url, callback) {
    fetch(API + url)
        .then(resposta => resposta.json())
        .then(callback);
}


function enviar(url, dados, callback) {
    fetch(API + url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(dados)
    })
        .then(resposta => resposta.json())
        .then(callback);
}


function cadastrarLivro() {
    const titulo = document.getElementById("t").value;
    const autor = document.getElementById("a").value;
    const ano = document.getElementById("y").value;
    const anoAtual = new Date().getFullYear();

    if (titulo.length < 3) {
        alert("Título muito curto");
        return;
    }

    if (autor === "") {
        alert("Informe o autor");
        return;
    }

    if (ano < ANO_MINIMO_LIVRO || ano > anoAtual) {
        alert("Ano inválido");
        return;
    }

    enviar("/livros", {
        titulo: titulo,
        autor: autor,
        ano: ano
    }, function (resposta) {
        alert(resposta.msg);

        if (resposta.ok === 1) {
            document.getElementById("t").value = "";
            document.getElementById("a").value = "";
            document.getElementById("y").value = "";
            mostrarLista(abaAtual);
        }
    });
}


function mostrarLista(tipoLista) {
    abaAtual = tipoLista;

    buscar("/lista/" + tipoLista, function (lista) {
        if (tipoLista === "todos" || tipoLista === "disp") {
            mostrarLivros(lista);
        } else {
            mostrarEmprestimos(lista);
        }
    });
}


function mostrarLivros(livros) {
    let tabela = "<tr>";
    tabela += "<th>ID</th>";
    tabela += "<th>Título</th>";
    tabela += "<th>Autor</th>";
    tabela += "<th>Ano</th>";
    tabela += "<th>Status</th>";
    tabela += "<th></th>";
    tabela += "</tr>";

    for (let i = 0; i < livros.length; i++) {
        const livro = livros[i];
        let botao = "";

        if (livro.status === "Disponível") {
            botao = "<button onclick=\"emprestarLivro(";
            botao += livro.id + ")\">Emprestar</button>";
        }

        tabela += "<tr>";
        tabela += "<td>" + livro.id + "</td>";
        tabela += "<td>" + livro.titulo + "</td>";
        tabela += "<td>" + livro.autor + "</td>";
        tabela += "<td>" + livro.ano + "</td>";
        tabela += "<td>" + livro.status + "</td>";
        tabela += "<td>" + botao + "</td>";
        tabela += "</tr>";
    }

    if (livros.length === 0) {
        tabela = "<tr><td>Nenhum registro.</td></tr>";
    }

    document.getElementById("tb").innerHTML = tabela;
}


function mostrarEmprestimos(emprestimos) {
    let tabela = "<tr>";
    tabela += "<th>Livro</th>";
    tabela += "<th>Leitor</th>";
    tabela += "<th>Empréstimo</th>";
    tabela += "<th>Previsto</th>";
    tabela += "<th>Devolvido</th>";
    tabela += "<th>Multa</th>";
    tabela += "<th></th>";
    tabela += "</tr>";

    for (let i = 0; i < emprestimos.length; i++) {
        const emprestimo = emprestimos[i];
        const classeAtrasado = emprestimo.atrasado
            ? " class=\"atrasado\""
            : "";

        const dataDevolucao = emprestimo.data_devolucao
            ? emprestimo.data_devolucao
            : "-";

        const multa = emprestimo.multa
            ? "R$ " + emprestimo.multa
            : "-";

        let botao = "";

        if (!emprestimo.data_devolucao) {
            botao = "<button onclick=\"devolverLivro(";
            botao += emprestimo.id + ")\">Devolver</button>";
        }

        tabela += "<tr" + classeAtrasado + ">";
        tabela += "<td>" + emprestimo.titulo + "</td>";
        tabela += "<td>" + emprestimo.usuario + "</td>";
        tabela += "<td>" + emprestimo.data_emprestimo + "</td>";
        tabela += "<td>" + emprestimo.data_prevista + "</td>";
        tabela += "<td>" + dataDevolucao + "</td>";
        tabela += "<td>" + multa + "</td>";
        tabela += "<td>" + botao + "</td>";
        tabela += "</tr>";
    }

    if (emprestimos.length === 0) {
        tabela = "<tr><td>Nenhum registro.</td></tr>";
    }

    document.getElementById("tb").innerHTML = tabela;
}


function emprestarLivro(livroId) {
    const usuario = prompt("Nome do leitor:");

    if (!usuario) {
        return;
    }

    enviar("/emprestar", {
        id: livroId,
        user: usuario
    }, function (resposta) {
        alert(resposta.msg);
        mostrarLista(abaAtual);
    });
}


function devolverLivro(emprestimoId) {
    if (!confirm("Confirmar devolução?")) {
        return;
    }

    enviar("/devolver", {
        id: emprestimoId
    }, function (resposta) {
        alert(resposta.msg);
        mostrarLista(abaAtual);
    });
}


mostrarLista("todos");