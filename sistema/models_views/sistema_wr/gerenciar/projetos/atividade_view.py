from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel, AtividadeAnexoModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_prioridade_model import PrioridadeAtividadeModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_andamento_model import AndamentoAtividadeModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_model import SolicitacaoAtividadeModel
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
from sistema._utilitarios import *
from datetime import datetime
import os
from werkzeug.utils import secure_filename


# Configurações de upload
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'rtf'},
    'compressed': {'zip', 'rar', '7z'},
    'other': {'csv'}
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Verifica se o arquivo é permitido baseado nas extensões configuradas"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    # Verifica em todas as categorias
    for extensions in ALLOWED_EXTENSIONS.values():
        if ext in extensions:
            return True
    return False


def get_file_type(filename):
    """Determina o tipo do arquivo baseado na extensão"""
    if '.' not in filename:
        return 'other'
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return 'other'


def get_cor_prioridade(prioridade_id):
    """Retorna a cor do badge baseada na prioridade"""
    cores = {
        1: 'danger',   # Alta
        2: 'warning',  # Média
        3: 'primary',  # Baixa
        4: 'secondary' # Muito baixa
    }
    return cores.get(prioridade_id, 'secondary')


def get_cor_situacao(situacao_id):
    """Retorna a cor do badge baseada na situação"""
    cores = {
        1: 'secondary', # Não iniciada
        2: 'warning',   # Em andamento
        3: 'success',   # Concluída
        4: 'danger',    # Cancelada
        5: 'info'       # Pausada
    }
    return cores.get(situacao_id, 'secondary')


@app.route("/gerenciar/atividades/anexo/download/<int:anexo_id>")
@login_required
@requires_roles
def atividade_download_anexo(anexo_id):
    anexo = AtividadeAnexoModel.query.filter(
        AtividadeAnexoModel.id == anexo_id,
        AtividadeAnexoModel.deletado == False
    ).first()
    
    if not anexo:
        flash(("Anexo não encontrado!", "warning"))
        referrer = request.referrer
        if referrer and 'atividade' in referrer:
            return redirect(referrer)
        return redirect(url_for("atividades_listar"))
    
    # Encontra o caminho correto do arquivo
    def encontrar_arquivo():
        caminhos_teste = [
            anexo.caminho_arquivo,
            os.path.join(os.getcwd(), anexo.caminho_arquivo),
            anexo.caminho_arquivo if os.path.isabs(anexo.caminho_arquivo) else None
        ]
        
        for caminho in caminhos_teste:
            if caminho and os.path.exists(caminho):
                # Garante que e retornado o caminho absoluto para o send_file
                return os.path.abspath(caminho)
        
        return None
    
    caminho_arquivo = encontrar_arquivo()
    
    if not caminho_arquivo:
        flash(("Arquivo não encontrado no servidor!", "warning"))
        return redirect(url_for("atividade_visualizar", atividade_id=anexo.atividade_id))
    
    try:
        # Faz o download com o caminho absoluto correto
        return send_file(
            caminho_arquivo,
            as_attachment=True,
            download_name=anexo.nome_original,
            mimetype=anexo.mime_type if anexo.mime_type else 'application/octet-stream'
        )
    except Exception as e:
        return redirect(url_for("atividade_visualizar", atividade_id=anexo.atividade_id))
    
    
@app.route("/gerenciar/atividades/visualizar/<int:atividade_id>")
@login_required
@requires_roles
def atividade_visualizar(atividade_id):
    atividade = AtividadeModel.obter_atividade_por_id(atividade_id)
    
    if not atividade:
        flash(("Atividade não encontrada!", "warning"))
        return redirect(url_for("atividades_listar"))
    
    # Buscar anexos da atividade
    anexos = atividade.anexos.filter(AtividadeAnexoModel.deletado == False).all()
    
    # Calcular estatísticas
    percentual_horas = atividade.percentual_horas
    percentual_horas_visual = min(percentual_horas, 100)  # Para a barra de progresso
    esta_atrasada = atividade.esta_atrasada
    
    # Informações do valor
    valor_real = atividade.valor_atividade_100 / 100 if atividade.valor_atividade_100 else 0
    
    # Formatação de datas
    data_prazo_formatada = None
    if atividade.data_prazo_conclusao:
        data_prazo_formatada = atividade.data_prazo_conclusao.strftime('%d/%m/%Y')
    
    data_cadastro_formatada = atividade.data_cadastro.strftime('%d/%m/%Y às %H:%M')
    data_alteracao_formatada = atividade.data_alteracao.strftime('%d/%m/%Y às %H:%M')
    
    # Status da atividade para cores dos badges
    status_cores = {
        'prioridade': get_cor_prioridade(atividade.prioridade_id),
        'situacao': get_cor_situacao(atividade.situacao_id)
    }
    
    return render_template(
        "sistema_wr/gerenciar/projetos/atividade_visualizar.html",
        atividade=atividade,
        anexos=anexos,
        percentual_horas=percentual_horas,
        percentual_horas_visual=percentual_horas_visual,
        esta_atrasada=esta_atrasada,
        valor_real=valor_real,
        data_prazo_formatada=data_prazo_formatada,
        data_cadastro_formatada=data_cadastro_formatada,
        data_alteracao_formatada=data_alteracao_formatada,
        status_cores=status_cores
    )
    
    
@app.route("/gerenciar/atividades")
@app.route("/gerenciar/atividades/<int:projeto_id>")
@login_required
@requires_roles
def atividades_listar(projeto_id=None):
    filtro_data_conclusao_inicio = request.args.get('data_conclusao_inicio')
    filtro_data_conclusao_fim = request.args.get('data_conclusao_fim')
    filtro_projeto = request.args.get('projeto_id', projeto_id)
    filtro_prioridade = request.args.get('prioridade_id')
    filtro_situacao = request.args.get('situacao_id')
    filtro_responsavel = request.args.get('responsavel_id')
    filtro_titulo = request.args.get('titulo')
    
    atividades = AtividadeModel.query.filter(
        AtividadeModel.deletado == False
    )
    
    if filtro_data_conclusao_inicio:
        try:
            data_inicio_obj = datetime.strptime(filtro_data_conclusao_inicio, '%Y-%m-%d').date()
            atividades = atividades.filter(AtividadeModel.data_prazo_conclusao >= data_inicio_obj)
        except ValueError:
            pass

    if filtro_data_conclusao_fim:
        try:
            data_fim_obj = datetime.strptime(filtro_data_conclusao_fim, '%Y-%m-%d').date()
            atividades = atividades.filter(AtividadeModel.data_prazo_conclusao <= data_fim_obj)
        except ValueError:
            pass
    
    if filtro_projeto:
        atividades = atividades.filter(AtividadeModel.projeto_id == filtro_projeto)
    
    if filtro_prioridade:
        atividades = atividades.filter(AtividadeModel.prioridade_id == filtro_prioridade)
    
    if filtro_situacao:
        atividades = atividades.filter(AtividadeModel.situacao_id == filtro_situacao)
    
    if filtro_responsavel:
        atividades = atividades.filter(AtividadeModel.usuario_execucao_id == filtro_responsavel)
    
    if filtro_titulo:
        atividades = atividades.filter(AtividadeModel.titulo.ilike(f"%{filtro_titulo}%"))
    
    atividades = atividades.order_by(
        AtividadeModel.prioridade_id.desc(),
        AtividadeModel.data_cadastro.desc()
    ).all()
    
    projetos = ProjetoModel.obter_projetos_asc_nome()
    
    prioridades = PrioridadeAtividadeModel.listar_prioridades_ativas()
    situacoes = AndamentoAtividadeModel.listar_andamentos_ativos()
    usuarios = UsuarioModel.obter_usuarios_asc_nome()
    
    return render_template(
        "sistema_wr/gerenciar/projetos/atividades_listar.html",
        atividades=atividades,
        projetos=projetos,
        prioridades=prioridades,
        situacoes=situacoes,
        usuarios=usuarios,
        filtros={
            'data_conclusao_inicio': filtro_data_conclusao_inicio,
            'data_conclusao_fim': filtro_data_conclusao_fim,
            'projeto_id': filtro_projeto,
            'prioridade_id': filtro_prioridade,
            'situacao_id': filtro_situacao,
            'responsavel_id': filtro_responsavel,
            'titulo': filtro_titulo
        }
    )


@app.route("/gerenciar/atividades/cadastrar", methods=["GET", "POST"])
@app.route("/gerenciar/atividades/cadastrar/<int:projeto_id>", methods=["GET", "POST"])
@app.route("/gerenciar/atividades/cadastrar/<int:projeto_id>/<int:solicitacao_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def atividade_cadastrar(projeto_id=None, solicitacao_id=None):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    projetos = ProjetoModel.obter_projetos_asc_nome()
    prioridades = PrioridadeAtividadeModel.listar_prioridades_ativas()
    situacoes = AndamentoAtividadeModel.listar_andamentos_ativos()
    usuarios = UsuarioModel.obter_usuarios_asc_nome()

    # Dados iniciais (podem vir de uma solicitação aceita)
    dados_corretos = {}
    solicitacao = None
    
    # Se veio de uma solicitação aceita, pré-preencher os dados
    if solicitacao_id:
        solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(solicitacao_id)
        if solicitacao and solicitacao.situacao_id == 3:  # 3 = Aceita
            dados_corretos = {
                "projetoId": str(solicitacao.projeto_id),
                "titulo": solicitacao.titulo,
                "descricao": solicitacao.descricao or "",
                "prioridadeId": "2",  # Prioridade média como padrão
                "situacaoId": "1"     # Não iniciada como padrão
            }
            projeto_id = solicitacao.projeto_id
        else:
            flash(("Solicitação não encontrada ou não aceita!", "warning"))
            return redirect(url_for("solicitacoes_atividade_listar"))

    if request.method == "POST":
        projeto_id = request.form["projetoId"]
        titulo = request.form["titulo"]
        descricao = request.form["descricao"]
        usuario_execucao_id = request.form.get("usuarioExecucaoId")
        horas_necessarias = request.form.get("horasNecessarias")
        data_prazo_conclusao = request.form.get("dataPrazoConclusao")
        valor_atividade = request.form.get("valorAtividade")
        prioridade_id = request.form["prioridadeId"]
        situacao_id = request.form["situacaoId"]

        campos = {
            "projetoId": ["Projeto", projeto_id],
            "titulo": ["Título", titulo],
            "prioridadeId": ["Prioridade", prioridade_id],
            "situacaoId": ["Situação", situacao_id]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if "validado" not in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        # Validação de horas necessárias
        horas_processadas = 0.0
        if horas_necessarias:
            try:
                horas_processadas = float(horas_necessarias.replace(',', '.'))
                if horas_processadas < 0:
                    validacao_campos_erros["horasNecessarias"] = "Horas não podem ser negativas"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["horasNecessarias"] = "Valor inválido para horas necessárias"
                gravar_banco = False

        # Validação de valor monetário
        valor_atividade_100 = 0
        if valor_atividade:
            try:
                valor_limpo = valor_atividade.replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor_float = float(valor_limpo)
                valor_atividade_100 = int(valor_float * 100)
                if valor_atividade_100 < 0:
                    validacao_campos_erros["valorAtividade"] = "Valor não pode ser negativo"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["valorAtividade"] = "Valor monetário inválido"
                gravar_banco = False

        # Validação da data
        data_prazo = None
        if data_prazo_conclusao:
            try:
                data_prazo = datetime.strptime(data_prazo_conclusao, '%Y-%m-%d').date()
            except ValueError:
                validacao_campos_erros["dataPrazoConclusao"] = "Data inválida"
                gravar_banco = False

        # Processar anexos
        arquivos_anexos = request.files.getlist('anexos[]')
        anexos_validos = []
        
        for arquivo in arquivos_anexos:
            if arquivo and arquivo.filename:
                if not allowed_file(arquivo.filename):
                    validacao_campos_erros["anexos"] = f"Tipo de arquivo não permitido: {arquivo.filename}"
                    gravar_banco = False
                    continue
                
                # Validar tamanho
                arquivo.seek(0, os.SEEK_END)
                file_size = arquivo.tell()
                arquivo.seek(0)  # Reset para o início
                
                if file_size > MAX_FILE_SIZE:
                    validacao_campos_erros["anexos"] = f"Arquivo muito grande: {arquivo.filename} (máx. 10MB)"
                    gravar_banco = False
                    continue
                
                anexos_validos.append(arquivo)

        # Se passou em todas as validações, gravar no banco
        if gravar_banco:
            try:
                # Criar atividade
                atividade = AtividadeModel(
                    projeto_id=projeto_id,
                    titulo=titulo,
                    descricao=descricao,  # imagens vai ser guardadas em base64, mudar no futuro
                    usuario_execucao_id=usuario_execucao_id if usuario_execucao_id else None,
                    horas_necessarias=horas_processadas,
                    horas_utilizadas=0,
                    data_prazo_conclusao=data_prazo,
                    valor_atividade_100=valor_atividade_100,
                    prioridade_id=prioridade_id,
                    situacao_id=situacao_id
                )
                
                db.session.add(atividade)
                db.session.flush()  # Para obter o ID da atividade
                
                # Processar anexos usando a função upload_arquivo existente
                anexos_processados = 0
                for arquivo in anexos_validos:
                    try:
                        # Usar a função upload_arquivo existente
                        arquivo_model = upload_arquivo(
                            arquivo=arquivo,
                            pasta_destino='UPLOADED_ANEXOS_ATIVIDADES',
                            nome_referencia=f"ativ_{atividade.id}"
                        )
                        
                        if arquivo_model:
                            # Criar registro na tabela de anexos da atividade
                            anexo = AtividadeAnexoModel(
                                atividade_id=atividade.id,
                                nome_arquivo=arquivo_model.nome,
                                nome_original=arquivo.filename,
                                caminho_arquivo=arquivo_model.caminho,
                                tipo_arquivo=get_file_type(arquivo.filename),
                                tamanho=int(arquivo_model.tamanho),
                                mime_type=arquivo.content_type
                            )
                            db.session.add(anexo)
                            anexos_processados += 1
                        else:
                            flash((f"Erro ao fazer upload do arquivo: {arquivo.filename}", "warning"))
                            
                    except Exception as e:
                        flash((f"Erro ao processar anexo {arquivo.filename}: {str(e)}", "warning"))
                        continue
                
                # Se veio de uma solicitação aceita, marcar como processada
                if solicitacao_id and solicitacao:
                    try:
                        # Criar um relacionamento ou log da conversão se necessário
                        # Por enquanto, mantemos a solicitação como aceita
                        pass
                    except Exception as e:
                        # Se der erro aqui, não afeta o cadastro da atividade
                        flash((f"Aviso: Erro ao processar solicitação: {str(e)}", "warning"))
                
                db.session.commit()
                
                # Mensagem de sucesso com informações dos anexos
                if solicitacao_id:
                    mensagem_sucesso = f"Atividade criada com sucesso a partir da solicitação!"
                else:
                    mensagem_sucesso = "Atividade cadastrada com sucesso!"
                
                if anexos_processados > 0:
                    mensagem_sucesso += f" {anexos_processados} arquivo(s) anexado(s)."
                
                flash((mensagem_sucesso, "success"))
                return redirect(url_for("atividades_listar", projeto_id=projeto_id))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao cadastrar atividade: {str(e)}", "warning"))
                gravar_banco = False

    return render_template(
        "sistema_wr/gerenciar/projetos/atividade_cadastrar.html",
        projetos=projetos,
        prioridades=prioridades,
        situacoes=situacoes,
        usuarios=usuarios,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
        projeto_id_url=projeto_id,
        solicitacao_id=solicitacao_id
    )


@app.route("/gerenciar/atividades/editar/<int:atividade_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def atividade_editar(atividade_id):
    """
    View para editar uma atividade existente
    """
    # Buscar a atividade
    atividade = AtividadeModel.obter_atividade_por_id(atividade_id)
    
    if not atividade:
        flash(("Atividade não encontrada!", "warning"))
        return redirect(url_for("atividades_listar"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    projetos = ProjetoModel.obter_projetos_asc_nome()
    prioridades = PrioridadeAtividadeModel.listar_prioridades_ativas()
    situacoes = AndamentoAtividadeModel.listar_andamentos_ativos()
    usuarios = UsuarioModel.obter_usuarios_asc_nome()

    if request.method == "POST":
        projeto_id = request.form.get("projetoId")
        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao")
        usuario_execucao_id = request.form.get("usuarioExecucaoId")
        horas_necessarias = request.form.get("horasNecessarias")
        data_prazo_conclusao = request.form.get("dataPrazoConclusao")
        valor_atividade = request.form.get("valorAtividade")
        prioridade_id = request.form.get("prioridadeId")
        situacao_id = request.form.get("situacaoId")

        campos = {
            "projetoId": ["Projeto", projeto_id],
            "titulo": ["Título", titulo],
            "prioridadeId": ["Prioridade", prioridade_id],
            "situacaoId": ["Situação", situacao_id]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if "validado" not in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        horas_necessarias_processadas = 0.0
        if horas_necessarias:
            try:
                horas_necessarias_processadas = float(horas_necessarias.replace(',', '.'))
                if horas_necessarias_processadas < 0:
                    validacao_campos_erros["horasNecessarias"] = "Horas não podem ser negativas"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["horasNecessarias"] = "Valor inválido para horas necessárias"
                gravar_banco = False

        valor_atividade_100 = 0
        if valor_atividade:
            try:
                valor_limpo = valor_atividade.replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor_float = float(valor_limpo)
                valor_atividade_100 = int(valor_float * 100)
                if valor_atividade_100 < 0:
                    validacao_campos_erros["valorAtividade"] = "Valor não pode ser negativo"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["valorAtividade"] = "Valor monetário inválido"
                gravar_banco = False

        # Validação da data
        data_prazo = None
        if data_prazo_conclusao:
            try:
                data_prazo = datetime.strptime(data_prazo_conclusao, '%Y-%m-%d').date()
            except ValueError:
                validacao_campos_erros["dataPrazoConclusao"] = "Data inválida"
                gravar_banco = False
                
        # Validação específica para conclusão de atividade
        if situacao_id == "4":  # 4 = Concluída
            from sistema.models_views.sistema_wr.gerenciar.projetos.lancamento_horas_model import LancamentoHorasModel
            
            # Verifica se existe pelo menos 1 lançamento de horas para esta atividade
            total_lancamentos = LancamentoHorasModel.query.filter(
                LancamentoHorasModel.atividade_id == atividade_id,
                LancamentoHorasModel.deletado == False
            ).count()
            
            if total_lancamentos == 0:
                flash((f"Atividade não pode ser concluída pois não tem registro de horas", "warning"))
                return redirect(url_for("atividade_editar", atividade_id=atividade_id))

        # Processa anexos (se houver novos uploads)
        arquivos_anexos = request.files.getlist('anexos[]')
        anexos_validos = []
        
        for arquivo in arquivos_anexos:
            if arquivo and arquivo.filename:
                if not allowed_file(arquivo.filename):
                    validacao_campos_erros["anexos"] = f"Tipo de arquivo não permitido: {arquivo.filename}"
                    gravar_banco = False
                    continue
                
                # Validar tamanho
                arquivo.seek(0, os.SEEK_END)
                file_size = arquivo.tell()
                arquivo.seek(0)  # Reset para o início
                
                if file_size > MAX_FILE_SIZE:
                    validacao_campos_erros["anexos"] = f"Arquivo muito grande: {arquivo.filename} (máx. 10MB)"
                    gravar_banco = False
                    continue
                
                anexos_validos.append(arquivo)
        if gravar_banco:
            try:
                # Atualizar dados da atividade
                atividade.projeto_id = projeto_id
                atividade.titulo = titulo
                atividade.descricao = descricao  # Mantém imagens Base64
                atividade.usuario_execucao_id = usuario_execucao_id if usuario_execucao_id else None
                atividade.horas_necessarias = horas_necessarias_processadas
                atividade.data_prazo_conclusao = data_prazo
                atividade.valor_atividade_100 = valor_atividade_100
                atividade.prioridade_id = prioridade_id
                atividade.situacao_id = situacao_id
                
                # Processa novos anexos (se houver)
                anexos_adicionados = 0
                for arquivo in anexos_validos:
                    try:
                        arquivo_model = upload_arquivo(
                            arquivo=arquivo,
                            pasta_destino='UPLOADED_ANEXOS_ATIVIDADES',
                            nome_referencia=f"ativ_{atividade.id}"
                        )
                        
                        if arquivo_model:
                            anexo = AtividadeAnexoModel(
                                atividade_id=atividade.id,
                                nome_arquivo=arquivo_model.nome,
                                nome_original=arquivo.filename,
                                caminho_arquivo=arquivo_model.caminho,
                                tipo_arquivo=get_file_type(arquivo.filename),
                                tamanho=int(arquivo_model.tamanho),
                                mime_type=arquivo.content_type
                            )
                            db.session.add(anexo)
                            anexos_adicionados += 1
                        else:
                            flash((f"Erro ao fazer upload do arquivo: {arquivo.filename}", "warning"))
                            
                    except Exception as e:
                        flash((f"Erro ao processar anexo {arquivo.filename}: {str(e)}", "warning"))
                        continue
                
                db.session.commit()
                
                mensagem_sucesso = "Atividade atualizada com sucesso!"
                if anexos_adicionados > 0:
                    mensagem_sucesso += f" {anexos_adicionados} novo(s) anexo(s) adicionado(s)."
                
                flash((mensagem_sucesso, "success"))
                return redirect(url_for("atividade_visualizar", atividade_id=atividade.id))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao atualizar atividade: {str(e)}", "error"))
                gravar_banco = False

    # Prepara dados corretos para preencher o formulário
    # Se houve erro, usa dados do formulário; senão, usa dados da atividade
    if request.method == "POST" and not gravar_banco:
        dados_corretos = request.form
    else:
        dados_corretos = {
            'projetoId': str(atividade.projeto_id),
            'titulo': atividade.titulo,
            'descricao': atividade.descricao or '',
            'usuarioExecucaoId': str(atividade.usuario_execucao_id) if atividade.usuario_execucao_id else '',
            'horasNecessarias': str(atividade.horas_necessarias).replace('.', ','),
            'dataPrazoConclusao': atividade.data_prazo_conclusao.strftime('%Y-%m-%d') if atividade.data_prazo_conclusao else '',
            'valorAtividade': f"R$ {atividade.valor_atividade_100 / 100:.2f}".replace('.', ',') if atividade.valor_atividade_100 else 0,
            'prioridadeId': str(atividade.prioridade_id),
            'situacaoId': str(atividade.situacao_id)
        }

    return render_template(
        "sistema_wr/gerenciar/projetos/atividade_editar.html",
        atividade=atividade,
        projetos=projetos,
        prioridades=prioridades,
        situacoes=situacoes,
        usuarios=usuarios,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )
    
    
@app.route("/gerenciar/atividades/anexo/remover/<int:anexo_id>", methods=["POST"])
@login_required
@requires_roles
def atividade_remover_anexo(anexo_id):
    """
    View para remover anexo da atividade via AJAX
    """
    try:
        anexo = AtividadeAnexoModel.query.filter(
            AtividadeAnexoModel.id == anexo_id,
            AtividadeAnexoModel.deletado == False
        ).first()
        
        if not anexo:
            return jsonify({
                'success': False,
                'message': 'Anexo não encontrado!'
            }), 404
        
        anexo.deletado = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Anexo removido com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao remover anexo: {str(e)}'
        }), 500


@app.route("/gerenciar/atividades/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def atividade_excluir(id):
    atividade = AtividadeModel.obter_atividade_por_id(id)
    
    if atividade:
        if atividade.situacao_id != 1:
            flash((f"Somente atividades 'Não iniciadas' podem ser excluidas!", "warning"))
            return redirect(url_for("atividades_listar"))
            
        atividade.deletado = True
        db.session.commit()
        
        flash((f"Atividade excluida com sucesso!", "success"))
        return redirect(url_for("atividades_listar"))
    
    else:
        flash((f"Atividade não encontrada!!", "warning"))
        return redirect(url_for("atividades_listar"))


@app.route("/gerenciar/atividades/duplicar/<int:id>", methods=["POST"])
@login_required
@requires_roles
def atividade_duplicar(id):
    atividade_original = AtividadeModel.obter_atividade_por_id(id)
    
    if not atividade_original:
        return jsonify({'success': False, 'message': 'Atividade não encontrada'}), 404
    
    try:
        # Criar nova atividade com dados da original
        nova_atividade = AtividadeModel(
            projeto_id=atividade_original.projeto_id,
            titulo=f"{atividade_original.titulo} (Cópia)",
            descricao=atividade_original.descricao,
            usuario_execucao_id=atividade_original.usuario_execucao_id,
            horas_necessarias=atividade_original.horas_necessarias,
            horas_utilizadas=0,  # Zerar horas utilizadas
            data_prazo_conclusao=atividade_original.data_prazo_conclusao,
            valor_atividade_100=atividade_original.valor_atividade_100,
            prioridade_id=atividade_original.prioridade_id,
            situacao_id=atividade_original.situacao_id
        )
        
        db.session.add(nova_atividade)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Atividade duplicada com sucesso!',
            'nova_atividade_id': nova_atividade.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao duplicar atividade: {str(e)}'
        }), 500
