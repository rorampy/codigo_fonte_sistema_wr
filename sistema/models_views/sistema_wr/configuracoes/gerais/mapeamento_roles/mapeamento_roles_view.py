import os
import json
from datetime import datetime

import mapeamento_roles as _mr_modulo
from sistema import app, requires_roles
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from logs_sistema import flask_logger
from sistema.models_views.sistema_wr.autenticacao.role_model import RoleModel


# Caminhos dos arquivos
MAPEAMENTO_ROLES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', '..', '..', 'mapeamento_roles.py'
)
HISTORICO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', '..', '..', 'map_roles_hist', 'map_roles_hist.json'
)
DESCRICOES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', '..', '..', 'map_roles_hist', 'map_roles_desc.json'
)

# Normalizar caminhos
MAPEAMENTO_ROLES_PATH = os.path.normpath(MAPEAMENTO_ROLES_PATH)
HISTORICO_PATH = os.path.normpath(HISTORICO_PATH)
DESCRICOES_PATH = os.path.normpath(DESCRICOES_PATH)


def _ler_mapeamento():
    """Lê o dict mapeamento_roles direto do arquivo .py via exec"""
    with open(MAPEAMENTO_ROLES_PATH, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    namespace = {}
    exec(conteudo, namespace)
    return namespace.get('mapeamento_roles', {})


def _salvar_mapeamento(mapeamento):
    """Reescreve o arquivo mapeamento_roles.py e atualiza o dict em memória"""
    linhas = ['# Defina todos os mapeamentos aqui\n']
    linhas.append('mapeamento_roles = {\n')
    
    for chave, roles in mapeamento.items():
        roles_str = ', '.join(f"'{r}'" for r in roles)
        linhas.append(f"    '{chave}': [{roles_str}],\n")
    
    linhas.append('}\n')
    
    with open(MAPEAMENTO_ROLES_PATH, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    
    # Atualiza o dict em memória para que @requires_roles reflita imediatamente
    _mr_modulo.mapeamento_roles.clear()
    _mr_modulo.mapeamento_roles.update(mapeamento)


def _ler_historico():
    """Lê o histórico de alterações do JSON"""
    try:
        with open(HISTORICO_PATH, 'r', encoding='utf-8') as f:
            conteudo = f.read().strip()
            if not conteudo:
                return []
            return json.loads(conteudo)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _salvar_historico(historico):
    """Salva o histórico de alterações no JSON"""
    with open(HISTORICO_PATH, 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def _ler_descricoes():
    """Lê as descrições de rotas do JSON"""
    try:
        with open(DESCRICOES_PATH, 'r', encoding='utf-8') as f:
            conteudo = f.read().strip()
            if not conteudo:
                return {}
            return json.loads(conteudo)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar_descricoes(descricoes):
    """Salva as descrições de rotas no JSON"""
    with open(DESCRICOES_PATH, 'w', encoding='utf-8') as f:
        json.dump(descricoes, f, ensure_ascii=False, indent=2)


def _registrar_historico(acao, chave, conteudo, justificativa='',
                         chave_anterior=None, estado_anterior=None, estado_novo=None):
    """Registra uma entrada no histórico com estado para reversão"""
    historico = _ler_historico()
    
    entrada = {
        'id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'usuario': f'{current_user.nome} {current_user.sobrenome}',
        'usuario_id': current_user.id,
        'acao': acao,
        'chave': chave,
        'conteudo': conteudo,
        'data_hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'revertido': False
    }
    
    if justificativa:
        entrada['justificativa'] = justificativa
    
    if chave_anterior and chave_anterior != chave:
        entrada['chave_anterior'] = chave_anterior
    
    # Armazenar estados para permitir reversão
    if estado_anterior is not None:
        entrada['estado_anterior'] = estado_anterior
    if estado_novo is not None:
        entrada['estado_novo'] = estado_novo
    
    # Inserir no início (mais recente primeiro)
    historico.insert(0, entrada)
    _salvar_historico(historico)


# ===================== ROTAS =====================

@app.route('/configuracoes/mapeamento-roles')
@login_required
@requires_roles
def map_roles_listar():
    mapeamento = _ler_mapeamento()
    historico = _ler_historico()
    descricoes = _ler_descricoes()
    roles_sistema = RoleModel.obter_roles_desc_id()
    
    return render_template(
        'sistema_wr/configuracao/mapeamento_roles/mapeamento_roles_listar.html',
        mapeamento=mapeamento,
        historico=historico[:100],
        descricoes=descricoes,
        roles_sistema=roles_sistema
    )


@app.route('/configuracoes/mapeamento-roles/adicionar', methods=['POST'])
@login_required
@requires_roles
def map_roles_adicionar():
    chave = request.form.get('chave_rota', '').strip()
    descricao = request.form.get('descricao', '').strip()
    roles_selecionadas = request.form.getlist('roles')
    
    if not chave:
        flash(('O nome da rota é obrigatório!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    if not roles_selecionadas:
        flash(('Selecione pelo menos uma role!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    mapeamento = _ler_mapeamento()
    
    if chave in mapeamento:
        flash(('Essa rota já existe no mapeamento!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    mapeamento[chave] = roles_selecionadas
    _salvar_mapeamento(mapeamento)
    
    # Salvar descrição se fornecida
    if descricao:
        descricoes = _ler_descricoes()
        descricoes[chave] = descricao
        _salvar_descricoes(descricoes)
    
    _registrar_historico(
        acao='adicionou',
        chave=chave,
        conteudo=str(roles_selecionadas),
        estado_anterior=None,
        estado_novo=roles_selecionadas
    )
    
    flask_logger.info(
        f'Usuario ID={current_user.id} adicionou mapeamento: {chave} -> {roles_selecionadas}'
    )
    
    flash(('Novo acesso adicionado com sucesso!', 'success'))
    return redirect(url_for('map_roles_listar'))


@app.route('/configuracoes/mapeamento-roles/editar', methods=['POST'])
@login_required
@requires_roles
def map_roles_editar():
    chave_original = request.form.get('chave_original', '').strip()
    chave_nova = request.form.get('chave_rota', '').strip()
    descricao = request.form.get('descricao', '').strip()
    justificativa = request.form.get('justificativa', '').strip()
    roles_selecionadas = request.form.getlist('roles')
    
    if not chave_nova:
        flash(('O nome da rota é obrigatório!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    if not roles_selecionadas:
        flash(('Selecione pelo menos uma role!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    mapeamento = _ler_mapeamento()
    
    if chave_original not in mapeamento:
        flash(('Rota original não encontrada!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    # Se renomeou a chave, verificar se a nova já existe
    if chave_nova != chave_original and chave_nova in mapeamento:
        flash(('Já existe uma rota com esse nome!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    # Guardar estado anterior para reversão
    roles_anteriores = list(mapeamento[chave_original])
    descricoes = _ler_descricoes()
    descricao_anterior = descricoes.get(chave_original, '')
    
    # Detectar o que de fato mudou
    mudancas = []
    
    if chave_nova != chave_original:
        mudancas.append(f'Renomeou rota: {chave_original} → {chave_nova}')
    
    roles_adicionadas = set(roles_selecionadas) - set(roles_anteriores)
    roles_removidas_set = set(roles_anteriores) - set(roles_selecionadas)
    
    if roles_adicionadas or roles_removidas_set:
        partes_roles = []
        if roles_adicionadas:
            partes_roles.append(f'+{", ".join(sorted(roles_adicionadas))}')
        if roles_removidas_set:
            partes_roles.append(f'-{", ".join(sorted(roles_removidas_set))}')
        mudancas.append(f'Roles: {" | ".join(partes_roles)}')
    
    if descricao != descricao_anterior:
        if not descricao_anterior and descricao:
            mudancas.append(f'Adicionou descrição: "{descricao}"')
        elif descricao_anterior and not descricao:
            mudancas.append('Removeu descrição')
        else:
            mudancas.append(f'Alterou descrição: "{descricao}"')
    
    # Salvar mapeamento mantendo a ordem
    novo_mapeamento = {}
    for k, v in mapeamento.items():
        if k == chave_original:
            novo_mapeamento[chave_nova] = roles_selecionadas
        else:
            novo_mapeamento[k] = v
    
    _salvar_mapeamento(novo_mapeamento)
    
    # Atualizar descrição
    if chave_original != chave_nova and chave_original in descricoes:
        descricoes.pop(chave_original)
    if descricao:
        descricoes[chave_nova] = descricao
    elif chave_nova in descricoes and not descricao:
        descricoes.pop(chave_nova, None)
    _salvar_descricoes(descricoes)
    
    # Registrar histórico somente se houve mudanças
    if mudancas:
        _registrar_historico(
            acao='editou',
            chave=chave_nova,
            conteudo=' | '.join(mudancas),
            justificativa=justificativa,
            chave_anterior=chave_original,
            estado_anterior=roles_anteriores,
            estado_novo=roles_selecionadas
        )
    
    flask_logger.info(
        f'Usuario ID={current_user.id} editou mapeamento: {chave_original} -> {chave_nova}: {roles_selecionadas}'
    )
    
    flash(('Acesso atualizado com sucesso!', 'success'))
    return redirect(url_for('map_roles_listar'))


@app.route('/configuracoes/mapeamento-roles/excluir', methods=['POST'])
@login_required
@requires_roles
def map_roles_excluir():
    chave = request.form.get('chave_rota', '').strip()
    justificativa = request.form.get('justificativa', '').strip()
    
    if not chave:
        flash(('Rota não informada!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    mapeamento = _ler_mapeamento()
    
    if chave not in mapeamento:
        flash(('Rota não encontrada no mapeamento!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    roles_removidas = list(mapeamento.pop(chave))
    _salvar_mapeamento(mapeamento)
    
    # Remover descrição se existir
    descricoes = _ler_descricoes()
    descricoes.pop(chave, None)
    _salvar_descricoes(descricoes)
    
    _registrar_historico(
        acao='removeu',
        chave=chave,
        conteudo=str(roles_removidas),
        justificativa=justificativa,
        estado_anterior=roles_removidas,
        estado_novo=None
    )
    
    flask_logger.info(
        f'Usuario ID={current_user.id} removeu mapeamento: {chave}'
    )
    
    flash(('Acesso removido com sucesso!', 'success'))
    return redirect(url_for('map_roles_listar'))


@app.route('/configuracoes/mapeamento-roles/reverter', methods=['POST'])
@login_required
@requires_roles
def map_roles_reverter():
    """Reverte uma alteração específica do histórico"""
    hist_id = request.form.get('hist_id', '').strip()
    
    if not hist_id:
        flash(('ID do histórico não informado!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    historico = _ler_historico()
    
    # Encontrar a entrada pelo ID
    entrada = None
    for item in historico:
        if item.get('id') == hist_id:
            entrada = item
            break
    
    if not entrada:
        flash(('Registro de histórico não encontrado!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    if entrada.get('revertido'):
        flash(('Essa alteração já foi revertida!', 'warning'))
        return redirect(url_for('map_roles_listar'))
    
    mapeamento = _ler_mapeamento()
    acao = entrada['acao']
    chave = entrada['chave']
    chave_anterior = entrada.get('chave_anterior')
    estado_anterior = entrada.get('estado_anterior')
    
    try:
        if acao == 'adicionou':
            # Reverter adição = remover a rota
            if chave in mapeamento:
                mapeamento.pop(chave)
                _salvar_mapeamento(mapeamento)
                msg_reversao = f'Removeu rota "{chave}" (reversão de adição)'
            else:
                flash(('Rota não encontrada para reverter!', 'warning'))
                return redirect(url_for('map_roles_listar'))
        
        elif acao == 'removeu':
            # Reverter remoção = adicionar a rota de volta com roles anteriores
            if estado_anterior:
                if chave in mapeamento:
                    flash((f'A rota "{chave}" já existe no mapeamento atual. Não é possível restaurar.', 'warning'))
                    return redirect(url_for('map_roles_listar'))
                mapeamento[chave] = estado_anterior
                _salvar_mapeamento(mapeamento)
                msg_reversao = f'Restaurou rota "{chave}" com roles: {estado_anterior}'
            else:
                flash(('Não há dados suficientes para reverter esta remoção!', 'warning'))
                return redirect(url_for('map_roles_listar'))
        
        elif acao == 'editou':
            # Reverter edição = restaurar roles anteriores e nome anterior
            if estado_anterior is not None:
                chave_restaurar = chave_anterior if chave_anterior else chave
                
                # Se a chave foi renomeada, verificar conflito antes de restaurar
                if chave_anterior and chave_anterior != chave:
                    if chave_restaurar in mapeamento:
                        flash((f'A rota "{chave_restaurar}" já existe. Não é possível reverter a renomeação.', 'warning'))
                        return redirect(url_for('map_roles_listar'))
                    mapeamento.pop(chave, None)
                    mapeamento[chave_restaurar] = estado_anterior
                else:
                    mapeamento[chave] = estado_anterior
                
                _salvar_mapeamento(mapeamento)
                msg_reversao = f'Restaurou rota "{chave_restaurar}" ao estado anterior: {estado_anterior}'
            else:
                flash(('Não há dados suficientes para reverter esta edição!', 'warning'))
                return redirect(url_for('map_roles_listar'))
        
        else:
            flash(('Tipo de ação desconhecido!', 'warning'))
            return redirect(url_for('map_roles_listar'))
        
        # Marcar a entrada original como revertida
        for item in historico:
            if item.get('id') == hist_id:
                item['revertido'] = True
                item['revertido_por'] = f'{current_user.nome} {current_user.sobrenome}'
                item['revertido_em'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                break
        _salvar_historico(historico)
        
        # Registrar a reversão no histórico
        _registrar_historico(
            acao='reverteu',
            chave=chave,
            conteudo=msg_reversao
        )
        
        flask_logger.info(
            f'Usuario ID={current_user.id} reverteu alteração hist_id={hist_id}: {msg_reversao}'
        )
        
        flash(('Alteração revertida com sucesso!', 'success'))
    
    except Exception as e:
        flask_logger.error(f'Erro ao reverter alteração hist_id={hist_id}: {str(e)}')
        flash(('Erro ao reverter alteração!', 'danger'))
    
    return redirect(url_for('map_roles_listar'))
