from sistema._utilitarios import *

class ProcessadorVariaveisContrato:
    """Classe responsável por processar e substituir variáveis no conteúdo do contrato"""
    
    @staticmethod
    def substituir_variaveis(texto, contrato):
        chaves = [
            'CLIENTE_NOME', 'CLIENTE_IDENTIFICACAO', 'CONTRATO_DATA_INICIO', 'CONTRATO_DATA_FIM',
            'CONTRATO_OBSERVACOES', 'CONTRATO_ATIVO', 'CONTRATO_ASSINADO', 'CONTRATO_STATUS',
            'MODELO_CONTRATO_NOME', 'FORMA_PAGAMENTO_DESCRICAO', 'PRODUTO_DESCRICAO', 'VALOR_NEGOCIADO',
            'PERIODO', 'VIGENCIA_INICIO', 'VIGENCIA_FIM', 'CARTAO_CREDITO', 'NMRO_PARCELAS'
        ]

        """
        Substitui as variáveis no texto pelos valores correspondentes, usando as chaves padronizadas do sistema.
        """
        if not texto or not contrato:
            return texto

        from sistema import formatar_float_para_brl, formatar_data_para_brl
        variaveis = {
            'CLIENTE_NOME': getattr(contrato.cliente, 'identificacao', ''),
            'CLIENTE_IDENTIFICACAO': (
                ValidaDocs.insere_pontuacao_cpf(getattr(contrato.cliente, 'numero_documento', ''))
                if len(getattr(contrato.cliente, 'numero_documento', '')) == 11
                else ValidaDocs.insere_pontuacao_cnpj(getattr(contrato.cliente, 'numero_documento', ''))
            ),
            'CONTRATO_DATA_INICIO': formatar_data_para_brl(getattr(contrato.contrato_produto[0], 'vigencia_inicio', None)) if getattr(contrato.contrato_produto[0], 'vigencia_inicio', None) else '',
            'CONTRATO_DATA_FIM': formatar_data_para_brl(getattr(contrato.contrato_produto[0], 'vigencia_fim', None)) if getattr(contrato.contrato_produto[0], 'vigencia_fim', None) else '',
            'CONTRATO_OBSERVACOES': getattr(contrato, 'observacoes', ''),
            'CONTRATO_ATIVO': 'Sim' if getattr(contrato, 'ativo', False) else 'Não',
            'CONTRATO_ASSINADO': 'Sim' if getattr(contrato, 'contrato_assinado', False) else 'Não',
            'CONTRATO_STATUS': getattr(contrato, 'status_contrato', ''),
            'MODELO_CONTRATO_NOME': getattr(getattr(contrato, 'modelo_contrato', None), 'nome_modelo', ''),
            'FORMA_PAGAMENTO_DESCRICAO': getattr(getattr(contrato, 'forma_pagamento', None), 'descricao', ''),
            'VALOR_NEGOCIADO': formatar_float_para_brl(getattr(contrato.contrato_produto[0], 'valor_negociado', 0)) if getattr(contrato.contrato_produto[0], 'valor_negociado', None) is not None else '',
            'NMRO_PARCELAS': str(contrato.contrato_produto[0].nmro_parcelas) if hasattr(contrato, 'contrato_produto') and contrato.contrato_produto and hasattr(contrato.contrato_produto[0], 'nmro_parcelas') and contrato.contrato_produto[0].nmro_parcelas is not None else '',
        }

        produto = contrato.contrato_produto[0] if hasattr(contrato, 'contrato_produto') and contrato.contrato_produto else None
        if produto:
            variaveis.update({
                'PRODUTO_DESCRICAO': getattr(produto.produto, 'descricao', ''),
                'VIGENCIA_INICIO': produto.vigencia_inicio.strftime('%d/%m/%Y') if produto.vigencia_inicio else '',
                'VIGENCIA_FIM': produto.vigencia_fim.strftime('%d/%m/%Y') if produto.vigencia_fim else '',
                'CARTAO_CREDITO': 'Sim' if getattr(produto, 'cartao_credito', False) else 'Não'
            })
        else:
            variaveis.update({
                'PRODUTO_DESCRICAO': '',
                'VALOR_NEGOCIADO': '',
                'PERIODO': '',
                'VIGENCIA_INICIO': '',
                'VIGENCIA_FIM': '',
                'CARTAO_CREDITO': '',
                'NMRO_PARCELAS': '',
            })

        # Substitui as variáveis no texto
        for chave in chaves:
            valor = variaveis.get(chave, f'[{chave}]')
            texto = texto.replace(chave, str(valor) if valor is not None else f'[{chave}]')

        return texto
    
    @staticmethod
    def _numero_para_extenso(valor):
        """Converte número para extenso (implementação básica)"""
        # Esta é uma implementação básica, você pode usar uma biblioteca como python-money
        try:
            valor_int = int(valor)
            unidades = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
            dezenas = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
            
            if valor_int == 0:
                return 'zero reais'
            elif valor_int < 10:
                return f'{unidades[valor_int]} {"real" if valor_int == 1 else "reais"}'
            elif valor_int < 100:
                dezena = valor_int // 10
                unidade = valor_int % 10
                texto = dezenas[dezena]
                if unidade > 0:
                    texto += f' e {unidades[unidade]}'
                return f'{texto} reais'
            else:
                return f'{valor_int} reais'  # Para valores maiores, retorna apenas o número
        except:
            return f'{valor} reais'
    
    @staticmethod
    def _obter_nome_mes(numero_mes):
        """Retorna o nome do mês por extenso"""
        meses = [
            '', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
            'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
        ]
        return meses[numero_mes] if 1 <= numero_mes <= 12 else ''