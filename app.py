from flask import Flask,request,jsonify,send_from_directory
import sqlite3, datetime
app=Flask(__name__)

def db():
    c=sqlite3.connect('lib.db');c.row_factory=sqlite3.Row
    return c

def init():
    c=db()
    c.execute("create table if not exists books(id integer primary key autoincrement,t text,a text,s integer,y integer)")
    c.execute("create table if not exists loans(id integer primary key autoincrement,b integer,u text,d1 text,d2 text,d3 text,f real)")
    c.commit()

@app.route('/')
def index():
    return send_from_directory('static','index.html')

@app.route('/<path:f>')
def files(f):
    return send_from_directory('static',f)

# cadastra livro
@app.route('/api/livros',methods=['POST'])
def add():
    d=request.json
    if d:
        if 'titulo' in d and d['titulo']:
            if len(d['titulo'])>=3:
                if 'autor' in d and d['autor']:
                    if 'ano' in d and d['ano']:
                        if int(d['ano'])>1000 and int(d['ano'])<=datetime.date.today().year:
                            c=db()
                            c.execute("insert into books(t,a,s,y) values(?,?,0,?)",(d['titulo'].strip(),d['autor'].strip(),int(d['ano'])))
                            c.commit()
                            return jsonify({'ok':1,'msg':'Livro cadastrado!'})
                        else:
                            return jsonify({'ok':0,'msg':'Ano invalido'}),400
                    else:
                        return jsonify({'ok':0,'msg':'Informe o ano'}),400
                else:
                    return jsonify({'ok':0,'msg':'Informe o autor'}),400
            else:
                return jsonify({'ok':0,'msg':'Titulo muito curto'}),400
        else:
            return jsonify({'ok':0,'msg':'Informe o titulo'}),400
    else:
        return jsonify({'ok':0,'msg':'Dados invalidos'}),400

# lista tudo: todos, disp, emp, pend, dev
@app.route('/api/lista/<t>')
def lst(t):
    c=db();r=[]
    if t=='todos' or t=='disp':
        q="select * from books"
        if t=='disp': q+=" where s=0"
        for x in c.execute(q).fetchall():
            r.append({'id':x['id'],'titulo':x['t'],'autor':x['a'],'ano':x['y'],'status':'Disponivel' if x['s']==0 else 'Emprestado'})
    else:
        q="select l.*,b.t from loans l join books b on b.id=l.b"
        if t=='pend': q+=" where l.d3 is null"
        if t=='dev': q+=" where l.d3 is not null"
        for x in c.execute(q).fetchall():
            atr=False
            if x['d3'] is None and str(datetime.date.today())>x['d2']: atr=True
            r.append({'id':x['id'],'titulo':x['t'],'usuario':x['u'],'data_emprestimo':x['d1'],'data_prevista':x['d2'],'data_devolucao':x['d3'],'multa':x['f'],'atrasado':atr})
    return jsonify(r)

# empresta livro
@app.route('/api/emprestar',methods=['POST'])
def emprestimo():
    d=request.json
    c=db()
    b=c.execute("select * from books where id=?",(d['id'],)).fetchone()
    if b:
        if b['s']==0:
            if d.get('user') and d['user'].strip()!='':
                n=c.execute("select count(*) from loans where u=? and d3 is null",(d['user'],)).fetchone()[0]
                if n<3:
                    h=datetime.date.today()
                    v=h+datetime.timedelta(days=14)
                    c.execute("insert into loans(b,u,d1,d2) values(?,?,?,?)",(d['id'],d['user'].strip(),str(h),str(v)))
                    c.execute("update books set s=1 where id=?",(d['id'],))
                    c.commit()
                    return jsonify({'ok':1,'msg':'Emprestado! Devolver ate '+str(v)})
                else:
                    return jsonify({'ok':0,'msg':'Limite de 3 livros por leitor'}),400
            else:
                return jsonify({'ok':0,'msg':'Informe o nome do usuario'}),400
        else:
            return jsonify({'ok':0,'msg':'Livro ja emprestado'}),400
    else:
        return jsonify({'ok':0,'msg':'Livro nao encontrado'}),404

# devolve livro
@app.route('/api/devolver',methods=['POST'])
def giveBack():
    d=request.json
    c=db()
    l=c.execute("select * from loans where id=?",(d['id'],)).fetchone()
    if l and l['d3'] is None:
        h=datetime.date.today()
        atraso=(h-datetime.date.fromisoformat(l['d2'])).days
        multa=0
        if atraso>0: multa=atraso*2.5
        c.execute("update loans set d3=?,f=? where id=?",(str(h),multa,d['id']))
        c.execute("update books set s=0 where id=?",(l['b'],))
        c.commit()
        m='Livro devolvido!'
        if multa>0: m+=' Multa: R$ '+str(multa)
        return jsonify({'ok':1,'msg':m})
    return jsonify({'ok':0,'msg':'Emprestimo nao encontrado ou ja devolvido'}),400

if __name__=='__main__':
    init()
    app.run(debug=True)
