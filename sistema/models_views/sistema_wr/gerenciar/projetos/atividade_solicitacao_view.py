from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_historico_model import SolicitacaoAtividadeHistoricoRejeicaoModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_model import SolicitacaoAtividadeModel, SolicitacaoAtividadeAnexoModel
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_andamento_model import AndamentoAtividadeModel
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.sistema_wr.parametrizacao.variavel_sistema_model import VariavelSistemaModel
from sistema._utilitarios import *
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename


# Configurações de upload (mesmas do sistema de atividades)
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


def get_cor_situacao_solicitacao(situacao_id):
    """Retorna a cor do badge baseada na situação da solicitação"""
    cores = {
        7: 'warning',   # Em Análise
        8: 'danger',    # Rejeitada
        3: 'success',   # Aceita/Aprovada (usa o mesmo ID da atividade concluída)
    }
    return cores.get(situacao_id, 'secondary')


@app.route("/gerenciar/solicitacoes-atividades")
@login_required
def solicitacoes_atividade_listar():
    """Lista todas as solicitações de atividades com filtros"""

    #Opções do Radio
    opcaoRadioData = request.args.get('tipo_filtro')
    print('Data:', opcaoRadioData)
    
    #Novos Filtros por datas
    filtro_data_inicio = request.args.get('data_inicio', '').strip()
    filtro_data_fim = request.args.get('data_fim', '').strip()

    # Recuperar filtros da URL
    filtro_projeto = request.args.get('projeto_id')
    filtro_situacao = request.args.get('situacao_id')
    filtro_usuario = request.args.get('usuario_id')
    filtro_titulo = request.args.get('titulo')

    
    # Filtrar solicitações

    atividades = SolicitacaoAtividadeModel.query.filter(
        SolicitacaoAtividadeModel.deletado == False
    )


    if any([filtro_projeto, filtro_situacao, filtro_usuario, filtro_titulo]):
        if filtro_projeto and filtro_projeto.strip():
            atividades = atividades.filter(SolicitacaoAtividadeModel.projeto_id == filtro_projeto)

        if filtro_situacao and filtro_situacao.strip():
            atividades = atividades.filter(SolicitacaoAtividadeModel.situacao_id == filtro_situacao)

        if filtro_usuario and filtro_usuario.strip():
            atividades = atividades.filter(SolicitacaoAtividadeModel.usuario_solicitante_id == filtro_usuario)
        
        if filtro_titulo and filtro_titulo.strip():
            atividades = atividades.filter(SolicitacaoAtividadeModel.titulo.ilike(f'%{filtro_titulo}%'))

    if opcaoRadioData == 'solicitacao':
        

        if filtro_data_inicio:
            try:
                data_inicio_obj = datetime.strptime(filtro_data_inicio, '%Y-%m-%d')
                atividades = atividades.filter(SolicitacaoAtividadeModel.data_cadastro >= data_inicio_obj)
            except ValueError:
                flash(f"Erro no formato da data incio")  
        
        if filtro_data_fim:
            try:
                data_fim_obj = datetime.strptime(filtro_data_fim, '%Y-%m-%d')
                fim_limite = data_fim_obj.replace(hour=23, minute=59, second=59)

                
                atividades = atividades.filter(SolicitacaoAtividadeModel.data_cadastro <= fim_limite)

            except ValueError:
                flash(f"Erro no formato de data fim")
    
    if opcaoRadioData == 'limite':
        try:
            # Para filtros de data limite, calcular no Python (mais compatível)
            solicitacoes_base = atividades.all()
            ids_validos = []
            
            for solicitacao in solicitacoes_base:
                if not (solicitacao.data_cadastro and solicitacao.prazo_resposta_dias):
                    continue
                    
                # Calcular data limite da solicitação
                data_limite = solicitacao.data_cadastro + timedelta(days=solicitacao.prazo_resposta_dias)
                
                # Verificar filtros de data
                passa_filtro_inicio = True
                passa_filtro_fim = True
                
                if filtro_data_inicio:
                    try:
                        data_inicio_obj = datetime.strptime(filtro_data_inicio, '%Y-%m-%d')
                        inicio_limite = data_inicio_obj.replace(hour=0, minute=0, second=0)
                        passa_filtro_inicio = data_limite >= inicio_limite
                    except ValueError:
                        passa_filtro_inicio = False
                
                if filtro_data_fim:
                    try:
                        data_fim_obj = datetime.strptime(filtro_data_fim, '%Y-%m-%d')
                        fim_limite = data_fim_obj.replace(hour=23, minute=59, second=59)
                        passa_filtro_fim = data_limite <= fim_limite
                    except ValueError:
                        passa_filtro_fim = False
                
                # Se passou em ambos os filtros, adicionar à lista
                if passa_filtro_inicio and passa_filtro_fim:
                    ids_validos.append(solicitacao.id)
            
            # Refazer a query com os IDs válidos
            if ids_validos:
                atividades = SolicitacaoAtividadeModel.query.filter(
                    SolicitacaoAtividadeModel.deletado == False,
                    SolicitacaoAtividadeModel.id.in_(ids_validos)
                )
                
                # Reaplicar filtros básicos
                if filtro_projeto and filtro_projeto.strip():
                    atividades = atividades.filter(SolicitacaoAtividadeModel.projeto_id == filtro_projeto)
                if filtro_situacao and filtro_situacao.strip():
                    atividades = atividades.filter(SolicitacaoAtividadeModel.situacao_id == filtro_situacao)
                if filtro_usuario and filtro_usuario.strip():
                    atividades = atividades.filter(SolicitacaoAtividadeModel.usuario_solicitante_id == filtro_usuario)
                if filtro_titulo and filtro_titulo.strip():
                    atividades = atividades.filter(SolicitacaoAtividadeModel.titulo.ilike(f'%{filtro_titulo}%'))
            else:
                # Nenhuma solicitação atende aos critérios
                atividades = SolicitacaoAtividadeModel.query.filter(SolicitacaoAtividadeModel.id == -1)
                
        except Exception as e:
            print(f"Erro no filtro por data limite: {e}")
            flash("Erro ao aplicar filtro por data limite")
    
    # if filtro_data_fim:
    #     try:
    #         data_limite_selecionada = datetime.strptime(filtro_data_fim, '%Y-%m-%d')
            
    #         # Início do dia limite (00:00:00)
    #         inicio_limite = data_limite_selecionada.replace(hour=0, minute=0, second=0)
            
    #         # Fim do dia limite (23:59:59)
    #         fim_limite = data_limite_selecionada.replace(hour=23, minute=59, second=59)
            
    #         # data_alteracao deve estar entre (limite - 48h) para resultar no dia desejado
    #         data_alteracao_min = inicio_limite - timedelta(hours=48)
    #         data_alteracao_max = fim_limite - timedelta(hours=48)
            
    #         atividades = atividades.filter(
    #             SolicitacaoAtividadeModel.data_alteracao >= data_alteracao_min,
    #             SolicitacaoAtividadeModel.data_alteracao <= data_alteracao_max
    #         )
    #     except ValueError:
    #         flash(f"Erro no formato data fim")

    dados_corretos = {
        'projeto_id': filtro_projeto if filtro_projeto and filtro_projeto.strip() else None,
        'situacao_id': filtro_situacao if filtro_situacao and filtro_situacao.strip() else None,
        'usuario_id': filtro_usuario if filtro_usuario and filtro_usuario.strip() else None,
        'titulo': filtro_titulo if filtro_titulo and filtro_titulo.strip() else None,
        'data_conclusao_inicio': filtro_data_inicio,
        'data_limite_fim': filtro_data_fim
    }
    

    # Executar a query
    solicitacoes = atividades.order_by(SolicitacaoAtividadeModel.data_cadastro.desc()).all()
  

    # Dados para os filtros
    projetos = ProjetoModel.query.filter(
        ProjetoModel.deletado == False,
        ProjetoModel.ativo == True
    ).order_by(ProjetoModel.nome_projeto.asc()).all()
    
    # Situações específicas para solicitações
    situacoes = AndamentoAtividadeModel.query.filter(
        AndamentoAtividadeModel.id.in_([7, 8]),  # Em Análise e Rejeitada
        AndamentoAtividadeModel.deletado == False
    ).order_by(AndamentoAtividadeModel.id.asc()).all()
    
    usuarios = UsuarioModel.query.filter(
        UsuarioModel.deletado == False,
        UsuarioModel.ativo == True
    ).order_by(UsuarioModel.nome.asc()).all()
    
    return render_template(
        "sistema_wr/gerenciar/projetos/solicitacoes_atividade/solicitacoes_atividade_listar.html",
        solicitacoes=solicitacoes,
        projetos=projetos,
        situacoes=situacoes,
        usuarios=usuarios,
        dados_corretos=dados_corretos,
        get_cor_situacao=get_cor_situacao_solicitacao,
        filtros={
            'data_inicio': filtro_data_inicio,
            'data_fim': filtro_data_fim,
            'projeto_id': filtro_projeto,
            'situacao_id': filtro_situacao,
            'usuario_id': filtro_usuario,
            'titulo': filtro_titulo,
            'tipo_filtro': opcaoRadioData
        }
    )


@app.route("/gerenciar/solicitacoes-atividades/cadastrar", methods=["GET", "POST"])
@app.route("/gerenciar/solicitacoes-atividades/cadastrar/<int:projeto_id>", methods=["GET", "POST"])
@login_required
def solicitacao_atividade_cadastrar(projeto_id=None):
    """Cadastrar nova solicitação de atividade"""
    
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    # Buscar projetos ativos
    projetos = ProjetoModel.query.filter(
        ProjetoModel.deletado == False,
        ProjetoModel.ativo == True
    ).order_by(ProjetoModel.nome_projeto.asc()).all()
    
    if request.method == "POST":
        projeto_id = request.form["projetoId"]
        titulo = request.form["titulo"]
        descricao = request.form.get("descricao", "")

        if len(titulo) > 100:
            validacao_campos_erros["titulo"] = "Título deve ter no máximo 100 caracteres"
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))
        
        # Campos obrigatórios
        campos = {
            "projetoId": ["Projeto", projeto_id],
            "titulo": ["Título", titulo]
        }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))
        
        # Validar se o projeto existe e está ativo
        if projeto_id:
            projeto = ProjetoModel.query.filter(
                ProjetoModel.id == projeto_id,
                ProjetoModel.deletado == False,
                ProjetoModel.ativo == True
            ).first()
            
            if not projeto:
                validacao_campos_erros["projetoId"] = "Projeto não encontrado ou inativo"
                gravar_banco = False

        prazo_resposta_dias = 7  # Valor padrão
        try:
            variaveis = VariavelSistemaModel.obter_variaveis_de_sistema_por_id(1)
            if variaveis and hasattr(variaveis, 'prazo_atividades') and variaveis.prazo_atividades:
                prazo_resposta_dias = int(variaveis.prazo_atividades)
        except Exception as e:
            print(f"Erro ao obter variável de sistema: {e}")
        
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
                # Criar solicitação
                solicitacao = SolicitacaoAtividadeModel(
                    projeto_id=projeto_id,
                    titulo=titulo,
                    descricao=descricao,
                    usuario_solicitante_id=current_user.id,
                    situacao_id=7,  # Em Análise
                    prazo_resposta_dias=prazo_resposta_dias
                )
                
                db.session.add(solicitacao)
                db.session.flush()  # Para obter o ID da solicitação
                
                # Processar anexos
                anexos_processados = 0
                for arquivo in anexos_validos:
                    try:
                        # Usar a função upload_arquivo existente
                        arquivo_model = upload_arquivo(
                            arquivo=arquivo,
                            pasta_destino='UPLOADED_ANEXOS_SOLICITACOES',
                            nome_referencia=f"solic_{solicitacao.id}"
                        )
                        
                        if arquivo_model:
                            # Criar registro na tabela de anexos da solicitação
                            anexo = SolicitacaoAtividadeAnexoModel(
                                solicitacao_id=solicitacao.id,
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
                
                db.session.commit()
                
                # Mensagem de sucesso
                mensagem_sucesso = f"Solicitação de atividade cadastrada com sucesso! Prazo para resposta: {prazo_resposta_dias} dias"
                if anexos_processados > 0:
                    mensagem_sucesso += f" ({anexos_processados} anexo(s) adicionado(s))"
                
                flash((mensagem_sucesso, "success"))
                return redirect(url_for("solicitacoes_atividade_listar"))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao cadastrar solicitação: {str(e)}", "danger"))
                gravar_banco = False
    
    return render_template(
        "sistema_wr/gerenciar/projetos/solicitacoes_atividade/solicitacao_atividade_cadastrar.html",
        projetos=projetos,
        projeto_id_url=projeto_id,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form if request.method == "POST" else {}
    )
    

@app.route("/gerenciar/solicitacoes-atividades/visualizar/<int:id>")
@login_required
def atividade_solicitacao_visualizar(id):
    """Visualiza uma solicitação de atividade específica"""
    
    solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(id)
    
    if not solicitacao:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    return render_template(
        "sistema_wr/gerenciar/projetos/solicitacoes_atividade/solicitacao_atividade_visualizar.html",
        solicitacao=solicitacao
    )


@app.route("/gerenciar/solicitacoes-atividades/anexo/remover/<int:anexo_id>", methods=["POST"])
@login_required
@requires_roles
def solicitacoes_atividade_remover_anexo(anexo_id):
    """Remove um anexo de solicitação de atividade via AJAX"""
    
    try:
        anexo = SolicitacaoAtividadeAnexoModel.obter_anexo_por_id(anexo_id)
        
        if not anexo:
            return jsonify({
                'success': False,
                'message': 'Anexo não encontrado!'
            }), 404
        
        # Verificar se o usuário tem permissão (deve ser o solicitante)
        solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(anexo.solicitacao_id)
        
        if not solicitacao or solicitacao.usuario_solicitante_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Você não tem permissão para remover este anexo!'
            }), 403
        
        # Verificar se a solicitação pode ser editada (apenas rejeitadas)
        if solicitacao.situacao_id != 8:  # 8 = Rejeitada
            return jsonify({
                'success': False,
                'message': 'Anexos só podem ser removidos de solicitações rejeitadas!'
            }), 400
        
        # Marcar anexo como deletado (soft delete)
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
        

@app.route("/gerenciar/solicitacoes-atividades/editar/<int:id>", methods=["GET", "POST"])
@login_required
def atividade_solicitacao_editar(id):
    """Edita uma solicitação de atividade (apenas rejeitadas e pelo solicitante)"""
    
    solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(id)
    
    if not solicitacao:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    # Verificar permissões: apenas o solicitante pode editar solicitações rejeitadas
    if solicitacao.usuario_solicitante_id != current_user.id:
        flash(("Você não tem permissão para editar esta solicitação!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    if solicitacao.situacao_id != 8:  # 8 = Rejeitada
        flash(("Apenas solicitações rejeitadas podem ser editadas!", "warning"))
        return redirect(url_for("atividade_solicitacao_visualizar", id=id))
    
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    # Buscar projetos ativos
    projetos = ProjetoModel.query.filter(
        ProjetoModel.deletado == False,
        ProjetoModel.ativo == True
    ).order_by(ProjetoModel.nome_projeto.asc()).all()
    
    if request.method == "POST":
        projeto_id = request.form["projetoId"]
        titulo = request.form["titulo"]
        descricao = request.form.get("descricao", "")
        
        # Campos obrigatórios
        campos = {
            "projetoId": ["Projeto", projeto_id],
            "titulo": ["Título", titulo]
        }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))
        
        if gravar_banco:
            try:
                # Atualizar dados da solicitação
                solicitacao.projeto_id = projeto_id
                solicitacao.titulo = titulo
                solicitacao.descricao = descricao
                solicitacao.situacao_id = 7  # 7 = Em Análise (volta para análise)
                
                # Processar anexos se houver
                anexos = request.files.getlist('anexos[]')
                anexos_processados = 0
                
                for arquivo in anexos:
                    if arquivo and arquivo.filename and allowed_file(arquivo.filename):
                        try:
                            # Usar a função upload_arquivo existente
                            arquivo_model = upload_arquivo(
                                arquivo=arquivo,
                                pasta_destino='UPLOADED_ANEXOS_SOLICITACOES',
                                nome_referencia=f"solic_{solicitacao.id}"
                            )
                            
                            if arquivo_model:
                                # Criar registro na tabela de anexos da solicitação
                                anexo = SolicitacaoAtividadeAnexoModel(
                                    solicitacao_id=solicitacao.id,
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
                
                db.session.commit()
                
                mensagem_sucesso = "Solicitação atualizada com sucesso!"
                if anexos_processados > 0:
                    mensagem_sucesso += f" ({anexos_processados} anexo(s) adicionado(s))"
                
                flash((mensagem_sucesso, "success"))
                return redirect(url_for("atividade_solicitacao_visualizar", id=id))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao atualizar solicitação: {str(e)}", "danger"))
                gravar_banco = False
    
    # Preparar dados para o formulário
    if request.method == "POST" and not gravar_banco:
        dados_corretos = request.form
    else:
        dados_corretos = {
            'projetoId': str(solicitacao.projeto_id),
            'titulo': solicitacao.titulo,
            'descricao': solicitacao.descricao or ''
        }
    
    return render_template(
        "sistema_wr/gerenciar/projetos/solicitacoes_atividade/solicitacao_atividade_editar.html",
        solicitacao=solicitacao,
        projetos=projetos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )


@app.route("/gerenciar/solicitacoes-atividades/excluir/<int:id>", methods=["GET", "POST"])
@login_required
def atividade_solicitacao_excluir(id):
    """Exclui uma solicitação de atividade (apenas pelo solicitante ou root, e em situações específicas)"""
    
    solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(id)
    
    if not solicitacao:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    if solicitacao.usuario_solicitante_id != current_user.id and current_user.role.id != 1:
        flash(("Você não tem permissão para excluir esta solicitação!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    # Verificar se a situação permite exclusão (7 = Em Análise, 8 = Rejeitada)
    if solicitacao.situacao_id not in [7, 8]:
        flash(("Esta solicitação não pode ser excluída no estado atual!", "warning"))
        return redirect(url_for("atividade_solicitacao_visualizar", id=id))
    
    try:
        # Marcar como deletado (soft delete)
        solicitacao.deletado = True
        
        # Marcar anexos como deletados também
        for anexo in solicitacao.anexos:
            anexo.deletado = True
        
        db.session.commit()
        
        flash(("Solicitação excluída com sucesso!", "success"))
        
    except Exception as e:
        db.session.rollback()
        flash((f"Erro ao excluir solicitação: {str(e)}", "danger"))
    
    return redirect(url_for("solicitacoes_atividade_listar"))


@app.route("/gerenciar/solicitacoes-atividades/aceitar/<int:id>", methods=["POST"])
@login_required
def atividade_solicitacao_aceitar(id):
    """Aceita uma solicitação de atividade e a converte em atividade (apenas gestão)"""
    
    # Verificar se é gestão (role.id == 1)
    if current_user.role.id != 1:
        flash(("Você não tem permissão para aceitar solicitações!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(id)
    
    if not solicitacao:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    # Verificar se está em análise
    if solicitacao.situacao_id != 7:  # 7 = Em Análise
        flash(("Apenas solicitações em análise podem ser aceitas!", "warning"))
        return redirect(url_for("atividade_solicitacao_visualizar", id=id))
    
    try:
        # Importar model de atividade
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel, AtividadeAnexoModel
        
        # Criar nova atividade baseada na solicitação
        nova_atividade = AtividadeModel(
            projeto_id=solicitacao.projeto_id,
            titulo=solicitacao.titulo,
            prioridade_id=2,  # Prioridade média como padrão
            situacao_id=1,    # Não iniciada
            descricao=solicitacao.descricao,
            supervisor_id=None,  # Será definido posteriormente
            desenvolvedor_id=None,  # Será definido posteriormente  
            usuario_solicitante_id=solicitacao.usuario_solicitante_id,  # Definir o solicitante
            horas_necessarias=0.0,
            horas_utilizadas=0.0,
            data_prazo_conclusao=None,
            valor_atividade_100=0
        )
        
        db.session.add(nova_atividade)
        db.session.flush()  # Para obter o ID da nova atividade
        
        # Atualizar status da solicitação para aceita
        solicitacao.situacao_id = 3  # 3 = Aceita/Aprovada
        
        # Copiar anexos da solicitação para a atividade (se houver)
        anexos_copiados = 0
        
        for anexo_solicitacao in solicitacao.anexos:
            if not anexo_solicitacao.deletado:
                # Criar novo anexo para a atividade
                anexo_atividade = AtividadeAnexoModel(
                    atividade_id=nova_atividade.id,
                    nome_arquivo=anexo_solicitacao.nome_arquivo,
                    nome_original=anexo_solicitacao.nome_original,
                    caminho_arquivo=anexo_solicitacao.caminho_arquivo,
                    tipo_arquivo=anexo_solicitacao.tipo_arquivo,
                    tamanho=anexo_solicitacao.tamanho,
                    mime_type=anexo_solicitacao.mime_type
                )
                db.session.add(anexo_atividade)
                anexos_copiados += 1
        
        db.session.commit()
        
        mensagem_sucesso = f"Solicitação aceita com sucesso! Atividade #{nova_atividade.id} criada."
        if anexos_copiados > 0:
            mensagem_sucesso += f" ({anexos_copiados} anexo(s) copiado(s))"
        
        flash((mensagem_sucesso, "success"))
        
        # Redirecionar para a nova atividade criada
        return redirect(url_for("atividade_visualizar", atividade_id=nova_atividade.id))
        
    except Exception as e:
        db.session.rollback()
        flash((f"Erro ao aceitar solicitação: {str(e)}", "danger"))
        return redirect(url_for("atividade_solicitacao_visualizar", id=id))


@app.route("/gerenciar/solicitacoes-atividades/rejeitar/<int:id>", methods=["POST"])
@login_required
def atividade_solicitacao_rejeitar(id):
    """Rejeita uma solicitação de atividade com motivo (apenas gestão)"""
    
    # Verificar se é gestão (role.id == 1)
    if current_user.role.id != 1:
        return jsonify({'success': False, 'message': 'Você não tem permissão para rejeitar solicitações!'}), 403
    
    solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(id)
    
    if not solicitacao:
        return jsonify({'success': False, 'message': 'Solicitação não encontrada!'}), 404
    
    # Verificar se está em análise
    if solicitacao.situacao_id != 7:  # 7 = Em Análise
        return jsonify({'success': False, 'message': 'Apenas solicitações em análise podem ser rejeitadas!'}), 400
    
    try:
        # Obter dados do request JSON
        dados = request.get_json()
        motivo = dados.get('motivo', '').strip()
        
        if not motivo:
            return jsonify({'success': False, 'message': 'Motivo da rejeição é obrigatório!'}), 400
        
        # *** NOVO: Salvar no histórico de rejeições ***
        historico_rejeicao = SolicitacaoAtividadeHistoricoRejeicaoModel(
            solicitacao_id=solicitacao.id,
            motivo_rejeicao=motivo,
            usuario_rejeitou_id=current_user.id
        )
        db.session.add(historico_rejeicao)
        
        # Atualizar solicitação
        solicitacao.situacao_id = 8  # 8 = Rejeitada
        solicitacao.motivo_rejeicao = motivo  # Mantém o último motivo para exibição rápida
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Solicitação rejeitada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao rejeitar solicitação: {str(e)}'
        }), 500


@app.route("/gerenciar/solicitacoes-atividades/anexo/download/<int:anexo_id>")
@login_required
def atividade_solicitacao_download_anexo(anexo_id):
    """Download de anexo de solicitação de atividade"""
    
    anexo = SolicitacaoAtividadeAnexoModel.obter_anexo_por_id(anexo_id)
    
    if not anexo:
        flash(("Anexo não encontrado!", "warning"))
        referrer = request.referrer
        if referrer and 'solicitacao' in referrer:
            return redirect(referrer)
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    # Encontra o caminho correto do arquivo
    def encontrar_arquivo():
        caminhos_teste = [
            anexo.caminho_arquivo,
            os.path.join(os.getcwd(), anexo.caminho_arquivo),
            anexo.caminho_arquivo if os.path.isabs(anexo.caminho_arquivo) else None
        ]
        
        for caminho in caminhos_teste:
            if caminho and os.path.exists(caminho):
                return os.path.abspath(caminho)
        return None
    
    caminho_arquivo = encontrar_arquivo()
    
    if not caminho_arquivo:
        flash(("Arquivo não encontrado no servidor!", "warning"))
        return redirect(url_for("atividade_solicitacao_visualizar", id=anexo.solicitacao_id))
    
    try:
        return send_file(
            caminho_arquivo,
            as_attachment=True,
            download_name=anexo.nome_original,
            mimetype=anexo.mime_type if anexo.mime_type else 'application/octet-stream'
        )
    except Exception as e:
        flash((f"Erro ao fazer download do arquivo: {str(e)}", "warning"))
        return redirect(url_for("atividade_solicitacao_visualizar", id=anexo.solicitacao_id))


@app.route("/gerenciar/solicitacoes-atividades/historico-rejeicoes/<int:id>")
@login_required
def atividade_solicitacao_historico_rejeicoes(id):
    """Visualiza o histórico completo de rejeições de uma solicitação"""
    
    solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(id)
    
    if not solicitacao:
        flash(("Solicitação não encontrada!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    # Verificar se o usuário pode ver (solicitante ou gestão)
    if solicitacao.usuario_solicitante_id != current_user.id and current_user.role.id != 1:
        flash(("Você não tem permissão para ver este histórico!", "warning"))
        return redirect(url_for("solicitacoes_atividade_listar"))
    
    # Buscar histórico de rejeições
    historico_rejeicoes = SolicitacaoAtividadeHistoricoRejeicaoModel.listar_historico_por_solicitacao(id)
    
    return render_template(
        "sistema_wr/gerenciar/projetos/solicitacoes_atividade/solicitacao_atividade_historico_rejeicoes.html",
        solicitacao=solicitacao,
        historico_rejeicoes=historico_rejeicoes
    )
    

@app.route("/gerenciar/solicitacoes-atividades/ajax/historico-rejeicoes/<int:id>")
@login_required
def atividade_solicitacao_ajax_historico_rejeicoes(id):
    """Retorna histórico de rejeições em JSON para modal"""
    
    solicitacao = SolicitacaoAtividadeModel.obter_solicitacao_por_id(id)
    
    if not solicitacao:
        return jsonify({'success': False, 'message': 'Solicitação não encontrada!'}), 404
    
    # Verificar permissões
    if solicitacao.usuario_solicitante_id != current_user.id and current_user.role.id != 1:
        return jsonify({'success': False, 'message': 'Sem permissão!'}), 403
    
    try:
        # Buscar histórico
        historico_rejeicoes = SolicitacaoAtividadeHistoricoRejeicaoModel.listar_historico_por_solicitacao(id)
        
        # Converter para JSON
        historico_json = []
        for rejeicao in historico_rejeicoes:
            historico_json.append({
                'id': rejeicao.id,
                'motivo': rejeicao.motivo_rejeicao,
                'data_rejeicao': rejeicao.data_rejeicao.strftime('%d/%m/%Y às %H:%M'),
                'usuario_rejeitou': rejeicao.usuario_rejeitou.nome if rejeicao.usuario_rejeitou else 'Usuário não encontrado'
            })
        
        return jsonify({
            'success': True,
            'historico': historico_json,
            'total_rejeicoes': len(historico_json)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar histórico: {str(e)}'
        }), 500


@app.route("/gerenciar/solicitacoes-atividades/estatisticas")
@login_required
def atividade_solicitacao_estatisticas():
    """Exibe estatísticas das solicitações de atividades"""
    
    # Buscar dados para as estatísticas
    total_solicitacoes = SolicitacaoAtividadeModel.query.filter(
        SolicitacaoAtividadeModel.deletado == False
    ).count()
    
    solicitacoes_em_analise = SolicitacaoAtividadeModel.query.filter(
        SolicitacaoAtividadeModel.deletado == False,
        SolicitacaoAtividadeModel.situacao_id == 7  # Em análise
    ).count()
    
    solicitacoes_aceitas = SolicitacaoAtividadeModel.query.filter(
        SolicitacaoAtividadeModel.deletado == False,
        SolicitacaoAtividadeModel.situacao_id == 3  # Aceitas
    ).count()
    
    solicitacoes_rejeitadas = SolicitacaoAtividadeModel.query.filter(
        SolicitacaoAtividadeModel.deletado == False,
        SolicitacaoAtividadeModel.situacao_id == 8  # Rejeitadas
    ).count()
    
    return render_template(
        "sistema_wr/gerenciar/projetos/solicitacoes_atividade/estatisticas_solicitacoes.html",
        total_solicitacoes=total_solicitacoes,
        solicitacoes_em_analise=solicitacoes_em_analise,
        solicitacoes_aceitas=solicitacoes_aceitas,
        solicitacoes_rejeitadas=solicitacoes_rejeitadas
    )


@app.route("/gerenciar/solicitacoes-atividades/buscar-por-motivo")
@login_required
def atividade_solicitacao_buscar_por_motivo():
    """Busca solicitações por motivo de rejeição via AJAX"""
    
    motivo = request.args.get('motivo', '').strip()
    
    if not motivo:
        return jsonify({
            'success': False,
            'message': 'Termo de busca é obrigatório!'
        }), 400
    
    try:
        # Buscar no histórico de rejeições
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_historico_model import SolicitacaoAtividadeHistoricoRejeicaoModel
        
        # Buscar rejeições que contenham o termo no motivo
        historico_rejeicoes = SolicitacaoAtividadeHistoricoRejeicaoModel.query.filter(
            SolicitacaoAtividadeHistoricoRejeicaoModel.motivo_rejeicao.ilike(f'%{motivo}%'),
            SolicitacaoAtividadeHistoricoRejeicaoModel.deletado == False
        ).order_by(
            SolicitacaoAtividadeHistoricoRejeicaoModel.data_rejeicao.desc()
        ).limit(20).all()  # Limitar a 20 resultados
        
        # Montar resultados
        resultados = []
        for rejeicao in historico_rejeicoes:
            solicitacao = rejeicao.solicitacao
            if solicitacao and not solicitacao.deletado:
                resultados.append({
                    'id': solicitacao.id,
                    'titulo': solicitacao.titulo,
                    'projeto': solicitacao.projeto.nome_projeto if solicitacao.projeto else 'N/A',
                    'motivo': rejeicao.motivo_rejeicao,
                    'data_rejeicao': rejeicao.data_rejeicao.strftime('%d/%m/%Y às %H:%M'),
                    'usuario_rejeitou': rejeicao.usuario_rejeitou.nome if rejeicao.usuario_rejeitou else 'N/A',
                    'url': url_for('atividade_solicitacao_visualizar', id=solicitacao.id)
                })
        
        return jsonify({
            'success': True,
            'total': len(resultados),
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar: {str(e)}'
        }), 500


@app.template_filter('adicionar_horas')
def adicionar_horas_filter(data, horas):
    """Filtro para adicionar horas a uma data"""
    if data:
        return data + timedelta(hours=horas)
    return None

@app.template_filter('prazo_vencido')
def prazo_vencido_filter(data_cadastro, horas_prazo=None):
    """Verifica se o prazo foi vencido (data_alteracao + horas < agora)"""
    if data_cadastro and horas_prazo:
        data_limite = data_cadastro + timedelta(hours=horas_prazo)
        return datetime.now() > data_limite
    return False
