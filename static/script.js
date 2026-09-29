var B='/api';
var aba='todos';

function g(u,cb){fetch(B+u).then(r=>r.json()).then(cb)}
function p(u,d,cb){fetch(B+u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(r=>r.json()).then(cb)}

function cad(){
  var t=document.getElementById('t').value, a=document.getElementById("a").value, y=document.getElementById('y').value;
  if(t.length<3){alert('Titulo muito curto');return}
  if(a==''){alert('Informe o autor');return}
  if(y<1000||y>2026){alert('Ano invalido');return}
  p('/livros',{titulo:t,autor:a,ano:y},function(r){
    alert(r.msg)
    if(r.ok==1){
      document.getElementById('t').value='';document.getElementById('a').value='';document.getElementById('y').value='';
      show(aba)
    }
  })
}

function show(t){
  aba=t;
  g('/lista/'+t,function(l){
    var h='';
    if(t=='todos'||t=='disp'){
      h+='<tr><th>ID</th><th>Titulo</th><th>Autor</th><th>Ano</th><th>Status</th><th></th></tr>';
      for(var i=0;i<l.length;i++){
        h+='<tr><td>'+l[i].id+'</td><td>'+l[i].titulo+'</td><td>'+l[i].autor+'</td><td>'+l[i].ano+'</td><td>'+l[i].status+'</td>';
        if(l[i].status=='Disponivel') h+='<td><button onclick="emp('+l[i].id+')">Emprestar</button></td>'; else h+='<td></td>';
        h+='</tr>';
      }
    }else{
      h+='<tr><th>Livro</th><th>Leitor</th><th>Emprestimo</th><th>Previsto</th><th>Devolvido</th><th>Multa</th><th></th></tr>';
      for(var i=0;i<l.length;i++){
        var c=''; if(l[i].atrasado) c=' class="atrasado"';
        h+='<tr'+c+'><td>'+l[i].titulo+'</td><td>'+l[i].usuario+'</td><td>'+l[i].data_emprestimo+'</td><td>'+l[i].data_prevista+'</td><td>'+(l[i].data_devolucao?l[i].data_devolucao:'-')+'</td><td>'+(l[i].multa?'R$ '+l[i].multa:'-')+'</td>';
        if(!l[i].data_devolucao) h+='<td><button onclick="dev('+l[i].id+')">Devolver</button></td>'; else h+='<td></td>';
        h+='</tr>';
      }
    }
    if(l.length==0) h='<tr><td>Nenhum registro.</td></tr>';
    document.getElementById('tb').innerHTML=h;
  })
}

function emp(id){
  var u=prompt('Nome do leitor:');
  if(u){
    p('/emprestar',{id:id,user:u},function(r){alert(r.msg);show(aba)})
  }
}

function dev(id){
  if(confirm('Confirmar devolucao?')){
    p('/devolver',{id:id},function(r){alert(r.msg);show(aba)})
  }
}

show('todos');
