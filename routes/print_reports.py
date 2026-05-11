#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rotas para Relatórios de Impressão - IPPEL
Funcionalidades específicas para gerar relatórios otimizados para impressão
"""

import sqlite3
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, session, redirect, url_for
from services.db import DB_PATH, get_db_connection, return_db_connection
from services.permissions import has_permission

print_reports = Blueprint('print_reports', __name__)

@print_reports.app_template_filter('parse_brl')
def _parse_brl_to_float(value):
    """Parse Brazilian currency string to float.
    
    Examples:
      'R$ 100,00' -> 100.0
      'R$ 1.234,56' -> 1234.56
      '100.00' -> 100.0
      None or '' -> 0.0
    """
    try:
        if value is None or value == '':
            return 0.0
        if isinstance(value, (int, float)):
            return abs(float(value))
        
        s = str(value).strip()
        if not s or s == '-':
            return 0.0
        
        # Remove currency symbols, quotes, and spaces
        for ch in ['R$', '$', ' ', '\"', '"', "'"]:
            s = s.replace(ch, '')
        
        if not s or s == '-':
            return 0.0
        
        # Count separators to determine format
        comma_count = s.count(',')
        dot_count = s.count('.')
        
        if comma_count > 0 and dot_count > 0:
            # Both present: determine which is decimal
            last_comma_pos = s.rfind(',')
            last_dot_pos = s.rfind('.')
            
            if last_comma_pos > last_dot_pos:
                # BR format: 1.234,56 (dot=thousands, comma=decimal)
                s = s.replace('.', '').replace(',', '.')
            else:
                # US format: 1,234.56 (comma=thousands, dot=decimal)
                s = s.replace(',', '')
        elif comma_count > 0:
            # Only comma: decimal separator (BR format)
            s = s.replace(',', '.')
        # else: only dot or no separator -> keep as is (US format)
        
        return float(s) if s else 0.0
    except Exception:
        return 0.0

# ===== Jinja filter: format numbers in BRL style (1.234,56) =====
@print_reports.app_template_filter('brl')
def _format_brl_number(value):
    """Return number formatted in Brazilian style without currency symbol.

    Examples:
      1234.5 -> '1.234,50'
      'R$ 3,45' -> '3,45'
    """
    try:
        # Normalize to float
        if value is None or value == '':
            num = 0.0
        elif isinstance(value, (int, float)):
            num = float(value)
        else:
            s = str(value).strip()
            # Remove currency and quotes/spaces
            for ch in ['R$', '$', ' ', '\"', '"', "'"]:
                s = s.replace(ch, '')
            # Decide how to parse depending on separators present
            if ',' in s and '.' in s:
                # Assume BR format: thousands '.' and decimal ','
                s = s.replace('.', '').replace(',', '.')
            elif ',' in s and '.' not in s:
                # Only comma present -> decimal comma
                s = s.replace(',', '.')
            else:
                # Only dot or none -> keep as is
                s = s
            num = float(s) if s not in ('', '-',) else 0.0

        # Format with thousands comma and dot decimal, then swap
        txt = f"{num:,.2f}"
        return txt.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return '0,00'

# With currency symbol
@print_reports.app_template_filter('brl_money')
def _format_brl_money(value):
    try:
        return f"R$ {_format_brl_number(value)}"
    except Exception:
        return 'R$ 0,00'
# Also expose a helper for direct use in templates if needed
@print_reports.app_context_processor
def _inject_brl_helpers():
    return {
        'format_brl': _format_brl_number,
        'format_brl_money': _format_brl_money,
    }

# ===== Função para remover duplicatas Máquina/Funcionário =====
def remove_duplicates_maquina_funcionario(rncs_list):
    """
    Remove duplicatas de RNCs quando Máquina e Funcionário têm o mesmo valor.
    
    Lógica:
    1. Agrupa RNCs por (responsavel, price)
    2. Se houver múltiplas RNCs com mesmo responsável e mesmo valor:
       - Verifica se há uma com 'Máquina' e outra com 'Funcionário' no título/descrição
       - Se sim: mantém apenas 'Funcionário', descarta 'Máquina'
    3. Caso contrário: mantém todas as RNCs
    
    Exemplo:
        Input:
            - RNC-001: João, R$ 1000, título="Máquina X"
            - RNC-002: João, R$ 1000, título="Funcionário João"
        Output:
            - RNC-002: João, R$ 1000, título="Funcionário João"
    """
    if not rncs_list:
        return []
    
    # Agrupar por (responsavel, price)
    from collections import defaultdict
    groups = defaultdict(list)
    
    for rnc in rncs_list:
        responsavel = rnc.get('responsavel') or rnc.get('creator_name') or 'Sistema'
        price = rnc.get('price', 0)
        
        # Normalizar price para float
        try:
            if isinstance(price, str):
                # Remover R$, espaços, vírgulas
                price_clean = price.replace('R$', '').replace(' ', '').replace(',', '').replace('"', '').replace("'", '')
                price_float = float(price_clean) if price_clean else 0.0
            else:
                price_float = float(price) if price else 0.0
        except:
            price_float = 0.0
        
        # Chave: (responsavel, price_arredondado)
        key = (responsavel, round(price_float, 2))
        groups[key].append(rnc)
    
    # Processar cada grupo
    result = []
    for (responsavel, price), group in groups.items():
        if len(group) == 1:
            # Apenas 1 RNC com esse responsável e valor → manter
            result.append(group[0])
        else:
            # Múltiplas RNCs → verificar se há Máquina + Funcionário
            has_maquina = False
            has_funcionario = False
            maquina_rnc = None
            funcionario_rnc = None
            
            for rnc in group:
                title = (rnc.get('title') or '').lower()
                description = (rnc.get('description') or '').lower()
                text = f"{title} {description}"
                
                if 'máquina' in text or 'maquina' in text:
                    has_maquina = True
                    maquina_rnc = rnc
                
                if 'funcionário' in text or 'funcionario' in text:
                    has_funcionario = True
                    funcionario_rnc = rnc
            
            if has_maquina and has_funcionario:
                # ✅ Duplicata detectada: Máquina + Funcionário com mesmo valor
                # Manter apenas Funcionário
                if funcionario_rnc:
                    result.append(funcionario_rnc)
                    print(f"🔍 Duplicata removida: {responsavel} - R$ {price:.2f} (mantido Funcionário, removido Máquina)")
                else:
                    # Fallback: manter todos
                    result.extend(group)
            else:
                # Não é caso Máquina+Funcionário → manter todos
                result.extend(group)
    
    print(f"📊 RNCs antes: {len(rncs_list)} | RNCs depois: {len(result)} | Removidas: {len(rncs_list) - len(result)}")
    return result

@print_reports.route('/report/print_rnc')
def print_rnc_report():
    """Gera relatório de RNCs otimizado para impressão"""
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    
    # Verificar permissão
    if not has_permission(session['user_id'], 'can_print_reports'):
        return "Você não tem permissão para imprimir relatórios", 403
    
    # Parâmetros da URL
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    format_type = request.args.get('format', 'detailed')
    
    if not start_date or not end_date:
        return "Parâmetros de data são obrigatórios", 400
    
    try:
        # Buscar RNCs no período
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query base para buscar RNCs
        query = """
            SELECT r.*, u.name as creator_name, u.department as creator_department,
                   au.name as assigned_user_name, au.department as assigned_department
            FROM rncs r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN users au ON r.assigned_user_id = au.id
            WHERE r.is_deleted = 0 
            AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
            ORDER BY r.created_at DESC
        """
        
        cursor.execute(query, (start_date, end_date))
        rncs = cursor.fetchall()
        
        # Obter colunas
        columns = [desc[0] for desc in cursor.description]
        rncs_list = [dict(zip(columns, rnc)) for rnc in rncs]
        
        # Estatísticas resumidas
        stats = calculate_report_stats(cursor, start_date, end_date)
        
        return_db_connection(conn)
        
        # Renderizar template baseado no formato
        if format_type == 'summary':
            return render_template('reports/print_summary.html', 
                                 rncs=rncs_list, 
                                 stats=stats,
                                 start_date=start_date,
                                 end_date=end_date,
                                 generated_at=datetime.now())
        elif format_type == 'charts':
            return render_template('reports/print_charts.html', 
                                 rncs=rncs_list, 
                                 stats=stats,
                                 start_date=start_date,
                                 end_date=end_date,
                                 generated_at=datetime.now())
        else:  # detailed
            return render_template('reports/print_detailed.html', 
                                 rncs=rncs_list, 
                                 stats=stats,
                                 start_date=start_date,
                                 end_date=end_date,
                                 generated_at=datetime.now())
                                 
    except Exception as e:
        return f"Erro ao gerar relatório: {str(e)}", 500

@print_reports.route('/reports/menu')
def reports_menu():
    """Menu de seleção de relatórios"""
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    
    # Permission check for reports access
    try:
        if not has_permission(session['user_id'], 'view_reports'):
            return redirect('/dashboard?error=access_denied')
    except Exception:
        return redirect('/dashboard?error=access_denied')
    return render_template('reports/reports_menu.html')

@print_reports.route('/reports/date_selection')
def date_selection():
    """Página de seleção de datas para relatórios"""
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    
    # Permission check for reports access
    try:
        if not has_permission(session['user_id'], 'view_reports'):
            return redirect('/dashboard?error=access_denied')
    except Exception:
        return redirect('/dashboard?error=access_denied')
    return render_template('reports/date_selection.html')

@print_reports.route('/reports/generate')
def generate_report():
    """Gera relatório de RNCs finalizados"""
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    # Permission check for reports generation
    try:
        if not has_permission(session['user_id'], 'view_reports'):
            return redirect('/dashboard?error=access_denied')
    except Exception:
        return redirect('/dashboard?error=access_denied')
    
    # Obter parâmetros da URL
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    report_type = request.args.get('type', 'finalized')
    
    # DEBUG: Mostrar parâmetros recebidos
    print(f"\n=== PARÂMETROS RECEBIDOS ===")
    print(f"start_date: {start_date}")
    print(f"end_date: {end_date}")
    print(f"report_type: {report_type}")
    print(f"============================\n")
    
    # Se não foram fornecidas datas, mostrar formulário de seleção
    if not start_date or not end_date:
        return render_template('reports/date_selection.html')
    
    try:
        # Buscar RNCs baseado no tipo de relatório
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # DEBUG: Verificar quantas RNCs existem no total
        cursor.execute("SELECT COUNT(*) FROM rncs WHERE is_deleted = 0")
        total_rncs = cursor.fetchone()[0]
        print(f"Total de RNCs ativas no banco: {total_rncs}")
        
        # DEBUG: Verificar RNCs no período
        cursor.execute("""
            SELECT COUNT(*), MIN(created_at), MAX(created_at) 
            FROM rncs 
            WHERE is_deleted = 0 
            AND DATE(created_at) BETWEEN ? AND ?
        """, (start_date, end_date))
        period_info = cursor.fetchone()
        print(f"RNCs no período {start_date} a {end_date}: {period_info[0]}")
        print(f"Data mais antiga: {period_info[1]}, Data mais recente: {period_info[2]}")
        
        if report_type == 'finalized':
            # Relatório de RNCs finalizados
            query = """
                SELECT r.*, 
                       u.name as creator_name, 
                       u.department as creator_department,
                       au.name as assigned_user_name, 
                       au.department as assigned_department,
                       COALESCE(
                           (SELECT name FROM groups WHERE id = CAST(r.area_responsavel AS INTEGER)),
                           (SELECT name FROM groups WHERE id = CAST(r.setor AS INTEGER)),
                           r.area_responsavel,
                           r.setor,
                           'Não informado'
                       ) as setor_nome
                FROM rncs r
                LEFT JOIN users u ON r.user_id = u.id
                LEFT JOIN users au ON r.assigned_user_id = au.id
                WHERE r.is_deleted = 0 
                AND r.status = 'Finalizado'
                AND COALESCE(r.area_responsavel, r.setor, '') NOT IN ('Não Definidos', 'Transporte', 'Filial', 'Usinagem plana')
                AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
                ORDER BY r.created_at DESC
            """
            template = 'reports/finalized_rncs_report.html'
            stats = calculate_finalized_stats_period(cursor, start_date, end_date)
            print(f"DEBUG - Stats calculados: total_finalizados={stats.get('total_finalizados')}, total_value={stats.get('total_value')}")
            
        elif report_type == 'total_detailed':
            # Relatório total detalhado
            # Obter filtros
            setor_filter = request.args.get('setor', 'todos')
            valor_min = request.args.get('valor_min', '')
            valor_max = request.args.get('valor_max', '')
            
            query = """
                SELECT r.*, 
                       u.name as creator_name, 
                       u.department as creator_department,
                       au.name as assigned_user_name, 
                       au.department as assigned_department,
                       COALESCE(causador_u.name, CAST(r.responsavel AS TEXT)) as causador_nome,
                       COALESCE(
                           (SELECT name FROM groups WHERE id = CAST(r.area_responsavel AS INTEGER)),
                           (SELECT name FROM groups WHERE id = CAST(r.setor AS INTEGER)),
                           r.area_responsavel,
                           r.setor,
                           r.ass_responsavel,
                           'Não informado'
                       ) as setor_responsavel,
                       r.signature_inspection_date as data_setor_responsavel,
                       r.signature_inspection_name as assinatura_responsavel
                FROM rncs r
                LEFT JOIN users u ON r.user_id = u.id
                LEFT JOIN users au ON r.assigned_user_id = au.id
                LEFT JOIN users causador_u ON CAST(r.responsavel AS TEXT) = CAST(causador_u.id AS TEXT)
                WHERE r.is_deleted = 0 
                AND CASE
                    WHEN r.created_at LIKE '__/__/____' THEN 
                        substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
                    ELSE 
                        DATE(r.created_at)
                END BETWEEN ? AND ?
                ORDER BY r.created_at DESC
            """
            template = 'reports/total_detailed_report.html'
            
            # Executar query
            cursor.execute(query, (start_date, end_date))
            rncs = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            rncs_list = [dict(zip(columns, rnc)) for rnc in rncs]
            
            # Função para normalizar setor
            def normalizar_setor(setor_nome):
                if setor_nome in ['Terceiros', 'Compras']:
                    return 'Suprimentos'
                elif setor_nome in ['Usinagem Plana', 'Usin. Cilíndrica CNC', 'Usin. Cilíndrica Convencional', 
                                    'Balanceamento', 'Caldeiraria de Carbono', 'Caldeiraria de Inox', 
                                    'Corte', 'Montagem', 'Pintura', 'Produção']:
                    return 'Produção'
                elif setor_nome == 'Não Definidos':
                    return 'Não informado'
                return setor_nome
            
            # Filtrar por setor se não for "todos"
            if setor_filter != 'todos':
                rncs_list = [r for r in rncs_list if normalizar_setor(r.get('setor_responsavel', 'Não informado')) == setor_filter]
            
            # Filtrar por valor
            if valor_min or valor_max:
                def get_price_value(rnc):
                    price = rnc.get('price', 0)
                    if price is None or price == '':
                        return 0.0
                    if isinstance(price, (int, float)):
                        return float(price)
                    s = str(price).strip()
                    for ch in ['R$', '$', ' ', '"', "'"]:
                        s = s.replace(ch, '')
                    if ',' in s and '.' in s:
                        s = s.replace('.', '').replace(',', '.')
                    elif ',' in s:
                        s = s.replace(',', '.')
                    try:
                        return float(s) if s else 0.0
                    except:
                        return 0.0
                
                if valor_min:
                    try:
                        min_val = float(valor_min)
                        rncs_list = [r for r in rncs_list if get_price_value(r) >= min_val]
                    except:
                        pass
                
                if valor_max:
                    try:
                        max_val = float(valor_max)
                        rncs_list = [r for r in rncs_list if get_price_value(r) <= max_val]
                    except:
                        pass
            
            # Calcular estatísticas baseadas na lista FILTRADA
            def calculate_filtered_stats_detailed(filtered_rncs):
                """Calcula estatísticas baseadas na lista de RNCs filtradas"""
                total = len(filtered_rncs)
                total_value = 0.0
                by_status = {}
                by_department = {}
                
                def parse_price(price):
                    if price is None or price == '':
                        return 0.0
                    if isinstance(price, (int, float)):
                        return float(price)
                    s = str(price).strip()
                    for ch in ['R$', '$', ' ', '"', "'"]:
                        s = s.replace(ch, '')
                    if ',' in s and '.' in s:
                        s = s.replace('.', '').replace(',', '.')
                    elif ',' in s:
                        s = s.replace(',', '.')
                    try:
                        return float(s) if s else 0.0
                    except:
                        return 0.0
                
                for rnc in filtered_rncs:
                    # Valor total
                    total_value += parse_price(rnc.get('price', 0))
                    
                    # Por status
                    status = rnc.get('status', 'Pendente')
                    by_status[status] = by_status.get(status, 0) + 1
                    
                    # Por departamento
                    dept = rnc.get('setor_responsavel') or rnc.get('creator_department') or 'Não informado'
                    by_department[dept] = by_department.get(dept, 0) + 1
                
                return {
                    'total_rncs': total,
                    'total_value': total_value,
                    'by_status': by_status,
                    'by_department': by_department,
                    'num_departments': len(by_department)
                }
            
            stats = calculate_filtered_stats_detailed(rncs_list)
            
            # DEBUG
            print(f"\n=== DEBUG RELATÓRIO TOTAL DETALHADO ===")
            print(f"Período: {start_date} a {end_date}")
            print(f"Filtro Setor: {setor_filter}")
            print(f"Filtro Valor Min: {valor_min}")
            print(f"Filtro Valor Max: {valor_max}")
            print(f"Total de RNCs: {len(rncs_list)}")
            print(f"=======================================\n")
            
            return_db_connection(conn)
            
            return render_template(template, 
                                 rncs_list=rncs_list,
                                 rncs=rncs_list,
                                 stats=stats,
                                 start_date=start_date,
                                 end_date=end_date,
                                 report_type=report_type,
                                 setor_filter=setor_filter,
                                 valor_min=valor_min,
                                 valor_max=valor_max,
                                 generated_at=datetime.now())
            
        elif report_type == 'by_operator':
            # Relatório por operador
            # Filtro de status baseado no parâmetro
            status_filter = request.args.get('status', 'both')  # 'finalized', 'pending', 'both'
            
            if status_filter == 'finalized':
                status_clause = "AND r.status = 'Finalizado'"
            elif status_filter == 'pending':
                status_clause = "AND r.status = 'Pendente'"
            else:  # both
                status_clause = "AND r.status IN ('Finalizado', 'Pendente')"
            
            query = f"""
                SELECT r.*, 
                       COALESCE(causador_u.name, u.name, r.responsavel) as creator_name,
                       COALESCE(g.name, r.area_responsavel, r.setor, 'Não informado') as creator_department,
                       COALESCE(causador_u.name, u.name, r.responsavel) as assigned_user_name,
                       COALESCE(g.name, r.area_responsavel, r.setor, 'Não informado') as assigned_department,
                       COALESCE(g.name, r.area_responsavel, r.setor, 'Não informado') as setor,
                       COALESCE(causador_u.name, u.name, r.responsavel) as responsavel
                FROM rncs r
                LEFT JOIN groups g ON (
                    CAST(r.area_responsavel AS TEXT) = CAST(g.id AS TEXT) OR
                    CAST(r.setor AS TEXT) = CAST(g.id AS TEXT)
                )
                LEFT JOIN users u ON CAST(r.responsavel AS TEXT) = CAST(u.id AS TEXT)
                LEFT JOIN users causador_u ON r.causador_user_id = causador_u.id
                WHERE r.is_deleted = 0 
                {status_clause}
                AND (r.responsavel IS NOT NULL OR r.causador_user_id IS NOT NULL)
                AND (r.responsavel != '' OR r.causador_user_id IS NOT NULL)
                AND CASE
                    WHEN r.created_at LIKE '__/__/____' THEN 
                        substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
                    ELSE 
                        DATE(r.created_at)
                END BETWEEN ? AND ?
                ORDER BY creator_department, creator_name, r.created_at DESC
            """
            template = 'reports/by_operator_report.html'
            stats = calculate_operator_stats_period(cursor, start_date, end_date, status_filter)
            
        elif report_type == 'by_sector':
            # Relatório por setor/departamento - resolve IDs numéricos via JOIN com groups
            # Obter filtros
            setor_filter = request.args.get('setor', 'todos')
            valor_min = request.args.get('valor_min', '')
            valor_max = request.args.get('valor_max', '')
            
            query = """
                SELECT r.*, 
                       COALESCE(
                           g.name,
                           CASE 
                               WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' 
                                   AND NOT (r.area_responsavel GLOB '[0-9]*')
                               THEN r.area_responsavel
                               ELSE NULL
                           END,
                           CASE 
                               WHEN r.setor IS NOT NULL AND r.setor != '' 
                                   AND NOT (r.setor GLOB '[0-9]*')
                               THEN r.setor
                               ELSE NULL
                           END,
                           'Não informado'
                       ) as creator_department,
                       COALESCE(u.name, r.responsavel) as creator_name,
                       COALESCE(
                           g.name,
                           CASE 
                               WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' 
                                   AND NOT (r.area_responsavel GLOB '[0-9]*')
                               THEN r.area_responsavel
                               ELSE NULL
                           END,
                           CASE 
                               WHEN r.setor IS NOT NULL AND r.setor != '' 
                                   AND NOT (r.setor GLOB '[0-9]*')
                               THEN r.setor
                               ELSE NULL
                           END,
                           'Não informado'
                       ) as assigned_department,
                       COALESCE(u.name, r.responsavel) as assigned_user_name,
                       COALESCE(u.name, r.responsavel) as responsavel,
                       COALESCE(
                           g.name,
                           CASE 
                               WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' 
                                   AND NOT (r.area_responsavel GLOB '[0-9]*')
                               THEN r.area_responsavel
                               ELSE NULL
                           END,
                           CASE 
                               WHEN r.setor IS NOT NULL AND r.setor != '' 
                                   AND NOT (r.setor GLOB '[0-9]*')
                               THEN r.setor
                               ELSE NULL
                           END,
                           'Outros'
                       ) as group_name
                FROM rncs r
                LEFT JOIN groups g ON (
                    r.area_responsavel IS NOT NULL 
                    AND r.area_responsavel GLOB '[0-9]*'
                    AND CAST(r.area_responsavel AS INTEGER) = g.id
                )
                LEFT JOIN users u ON CAST(r.responsavel AS TEXT) = CAST(u.id AS TEXT)
                WHERE r.is_deleted = 0 
                AND CASE
                    WHEN r.created_at LIKE '__/__/____' THEN 
                        substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
                    ELSE 
                        DATE(r.created_at)
                END BETWEEN ? AND ?
                ORDER BY group_name, creator_department, r.created_at DESC
            """
            template = 'reports/by_sector_report_simple.html'
            
            # Executar query
            cursor.execute(query, (start_date, end_date))
            rncs = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            rncs_list = [dict(zip(columns, rnc)) for rnc in rncs]
            
            # Função para normalizar setor
            def normalizar_setor(setor_nome):
                if setor_nome in ['Terceiros', 'Compras']:
                    return 'Suprimentos'
                elif setor_nome in ['Usinagem Plana', 'Usin. Cilíndrica CNC', 'Usin. Cilíndrica Convencional', 
                                    'Balanceamento', 'Caldeiraria de Carbono', 'Caldeiraria de Inox', 
                                    'Corte', 'Montagem', 'Pintura', 'Produção']:
                    return 'Produção'
                elif setor_nome == 'Não Definidos':
                    return 'Não informado'
                return setor_nome
            
            # Filtrar por setor se não for "todos"
            if setor_filter != 'todos':
                rncs_list = [r for r in rncs_list if normalizar_setor(r.get('group_name', 'Não informado')) == setor_filter]
            
            # Filtrar por valor
            if valor_min or valor_max:
                def get_price_value(rnc):
                    price = rnc.get('price', 0)
                    if price is None or price == '':
                        return 0.0
                    if isinstance(price, (int, float)):
                        return float(price)
                    # Parse BRL format
                    s = str(price).strip()
                    for ch in ['R$', '$', ' ', '"', "'"]:
                        s = s.replace(ch, '')
                    if ',' in s and '.' in s:
                        s = s.replace('.', '').replace(',', '.')
                    elif ',' in s:
                        s = s.replace(',', '.')
                    try:
                        return float(s) if s else 0.0
                    except:
                        return 0.0
                
                if valor_min:
                    try:
                        min_val = float(valor_min)
                        rncs_list = [r for r in rncs_list if get_price_value(r) >= min_val]
                    except:
                        pass
                
                if valor_max:
                    try:
                        max_val = float(valor_max)
                        rncs_list = [r for r in rncs_list if get_price_value(r) <= max_val]
                    except:
                        pass
            
            # Calcular estatísticas baseadas na lista FILTRADA
            def calculate_filtered_stats(filtered_rncs):
                """Calcula estatísticas baseadas na lista de RNCs filtradas"""
                total = len(filtered_rncs)
                total_value = 0.0
                by_status = {}
                by_department = {}
                
                def parse_price(price):
                    if price is None or price == '':
                        return 0.0
                    if isinstance(price, (int, float)):
                        return float(price)
                    s = str(price).strip()
                    for ch in ['R$', '$', ' ', '"', "'"]:
                        s = s.replace(ch, '')
                    if ',' in s and '.' in s:
                        s = s.replace('.', '').replace(',', '.')
                    elif ',' in s:
                        s = s.replace(',', '.')
                    try:
                        return float(s) if s else 0.0
                    except:
                        return 0.0
                
                for rnc in filtered_rncs:
                    # Valor total
                    total_value += parse_price(rnc.get('price', 0))
                    
                    # Por status
                    status = rnc.get('status', 'Pendente')
                    by_status[status] = by_status.get(status, 0) + 1
                    
                    # Por departamento
                    dept = rnc.get('group_name') or rnc.get('creator_department') or 'Não informado'
                    by_department[dept] = by_department.get(dept, 0) + 1
                
                return {
                    'total_rncs': total,
                    'total_value': total_value,
                    'by_status': by_status,
                    'by_department': by_department,
                    'num_departments': len(by_department)
                }
            
            stats = calculate_filtered_stats(rncs_list)
            
            # DEBUG
            print(f"\n=== DEBUG RELATÓRIO POR SETOR ===")
            print(f"Período: {start_date} a {end_date}")
            print(f"Filtro Setor: {setor_filter}")
            print(f"Filtro Valor Min: {valor_min}")
            print(f"Filtro Valor Max: {valor_max}")
            print(f"Total de RNCs: {len(rncs_list)}")
            print(f"=================================\n")
            
            return_db_connection(conn)
            
            return render_template(template, 
                                 rncs_list=rncs_list,
                                 rncs=rncs_list,
                                 stats=stats,
                                 start_date=start_date,
                                 end_date=end_date,
                                 report_type=report_type,
                                 setor_filter=setor_filter,
                                 valor_min=valor_min,
                                 valor_max=valor_max,
                                 generated_at=datetime.now())
            
        elif report_type == 'pauta_reuniao':
            # Relatório Pauta Reunião - JOIN com tabela GROUPS (não areas)
            # Obter filtros
            tipo_registro_filter = request.args.get('tipo_registro', 'ambos')  # 'ambos', 'ro', 'rnc'
            setor_filter = request.args.get('setor', 'todos')  # 'todos' ou nome do setor
            
            # Mapeamento de setores consolidados para filtro SQL
            setor_consolidado_map = {
                'Suprimentos': ['Suprimentos', 'Terceiros', 'Compras'],
                'Produção': ['Produção', 'Usinagem Plana', 'Usin. Cilíndrica CNC', 'Usin. Cilíndrica Convencional', 
                             'Balanceamento', 'Caldeiraria de Carbono', 'Caldeiraria de Inox', 
                             'Corte', 'Montagem', 'Pintura']
            }
            
            # Buscar RNCs
            query_rnc = """
                SELECT r.*, 
                       'RNC' as tipo_registro,
                       r.rnc_number as numero,
                       u.name as criador_nome,
                       r.drawing as numero_desenho,
                       COALESCE(causador_u.name, CAST(r.responsavel AS TEXT)) as causador_nome,
                       COALESCE(
                           g.name,
                           CASE 
                               WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' 
                                   AND NOT (r.area_responsavel GLOB '[0-9]*')
                               THEN r.area_responsavel
                               ELSE NULL
                           END,
                           CASE 
                               WHEN r.setor IS NOT NULL AND r.setor != '' 
                                   AND NOT (r.setor GLOB '[0-9]*')
                               THEN r.setor
                               ELSE NULL
                           END,
                           'Não informado'
                       ) as setor_ordem
                FROM rncs r
                LEFT JOIN groups g ON (
                    r.area_responsavel IS NOT NULL 
                    AND r.area_responsavel GLOB '[0-9]*'
                    AND CAST(r.area_responsavel AS INTEGER) = g.id
                )
                LEFT JOIN users u ON r.user_id = u.id
                LEFT JOIN users causador_u ON r.causador_user_id = causador_u.id
                WHERE r.is_deleted = 0 
                AND (
                    CASE
                        WHEN r.created_at LIKE '__/__/____' THEN 
                            substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
                        ELSE 
                            DATE(r.created_at)
                    END BETWEEN ? AND ?
                )
            """
            
            # Buscar R.Os
            query_ro = """
                SELECT r.*, 
                       'RO' as tipo_registro,
                       r.ro_number as numero,
                       r.description as description,
                       COALESCE(
                           g.name,
                           CASE 
                               WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' 
                                   AND NOT (r.area_responsavel GLOB '[0-9]*')
                               THEN r.area_responsavel
                               ELSE NULL
                           END,
                           CASE 
                               WHEN r.setor IS NOT NULL AND r.setor != '' 
                                   AND NOT (r.setor GLOB '[0-9]*')
                               THEN r.setor
                               ELSE NULL
                           END,
                           'Não informado'
                       ) as setor_ordem,
                       u.name as criador_nome,
                       COALESCE(causador_u.name, '') as causador_nome
                FROM ros r
                LEFT JOIN groups g ON (
                    r.area_responsavel IS NOT NULL 
                    AND r.area_responsavel GLOB '[0-9]*'
                    AND CAST(r.area_responsavel AS INTEGER) = g.id
                )
                LEFT JOIN users u ON r.user_id = u.id
                LEFT JOIN users causador_u ON r.causador_user_id = causador_u.id
                WHERE r.is_deleted = 0 
                AND (
                    CASE
                        WHEN r.created_at LIKE '__/__/____' THEN 
                            substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
                        ELSE 
                            DATE(r.created_at)
                    END BETWEEN ? AND ?
                )
            """
            
            # Buscar Garantias
            query_garantias = """
                SELECT g.*, 
                       'GARANTIA' as tipo_registro,
                       g.garantia_number as numero,
                       g.description as description,
                       g.item_fornecido as title,
                       g.cv as cv,
                       g.cv_date as cv_date,
                       g.client as client,
                       g.equipment as equipment,
                       g.quantity as quantity,
                       g.sector as causador_nome,
                       COALESCE(g.setor_causador, g.area_responsavel, 'Não informado') as setor_ordem,
                       u.name as criador_nome
                FROM garantias g
                LEFT JOIN users u ON g.user_id = u.id
                WHERE (g.is_deleted = 0 OR g.is_deleted IS NULL)
                AND (
                    CASE
                        WHEN g.created_at LIKE '__/__/____' THEN 
                            substr(g.created_at, 7, 4) || '-' || substr(g.created_at, 4, 2) || '-' || substr(g.created_at, 1, 2)
                        ELSE 
                            DATE(g.created_at)
                    END BETWEEN ? AND ?
                )
            """
            
            template = 'reports/pauta_reuniao_report.html'
            stats = {}
            
            rncs_list = []
            ros_list = []
            garantias_list = []
            
            # Buscar RNCs (se filtro permitir)
            if tipo_registro_filter in ['ambos', 'rnc', 'todos']:
                cursor.execute(query_rnc, (start_date, end_date))
                rncs = cursor.fetchall()
                columns_rnc = [desc[0] for desc in cursor.description]
                rncs_list = [dict(zip(columns_rnc, rnc)) for rnc in rncs]
            
            # Buscar R.Os (se filtro permitir)
            if tipo_registro_filter in ['ambos', 'ro', 'todos']:
                cursor.execute(query_ro, (start_date, end_date))
                ros = cursor.fetchall()
                columns_ro = [desc[0] for desc in cursor.description]
                ros_list = [dict(zip(columns_ro, ro)) for ro in ros]
            
            # Buscar Garantias (se filtro permitir)
            if tipo_registro_filter in ['garantias', 'todos']:
                cursor.execute(query_garantias, (start_date, end_date))
                garantias = cursor.fetchall()
                columns_garantias = [desc[0] for desc in cursor.description]
                garantias_list = [dict(zip(columns_garantias, g)) for g in garantias]
            
            # Aplicar filtro de setor (após consolidação)
            def normalizar_setor(setor_nome):
                """Normaliza o nome do setor para o consolidado"""
                if setor_nome in ['Terceiros', 'Compras']:
                    return 'Suprimentos'
                elif setor_nome in ['Usinagem Plana', 'Usin. Cilíndrica CNC', 'Usin. Cilíndrica Convencional', 
                                    'Balanceamento', 'Caldeiraria de Carbono', 'Caldeiraria de Inox', 
                                    'Corte', 'Montagem', 'Pintura', 'Produção']:
                    return 'Produção'
                elif setor_nome == 'Não Definidos':
                    return 'Não informado'
                return setor_nome
            
            # Filtrar por setor se não for "todos"
            if setor_filter != 'todos':
                rncs_list = [r for r in rncs_list if normalizar_setor(r.get('setor_ordem', 'Não informado')) == setor_filter]
                ros_list = [r for r in ros_list if normalizar_setor(r.get('setor_ordem', 'Não informado')) == setor_filter]
                garantias_list = [g for g in garantias_list if normalizar_setor(g.get('setor_ordem', 'Não informado')) == setor_filter]
            
            # Combinar RNCs, R.Os e Garantias
            combined_list = rncs_list + ros_list + garantias_list
            
            # DEBUG
            print(f"\n=== DEBUG RELATÓRIO PAUTA REUNIÃO ===")
            print(f"Período: {start_date} a {end_date}")
            print(f"Filtro Tipo: {tipo_registro_filter}")
            print(f"Filtro Setor: {setor_filter}")
            print(f"Total de RNCs encontradas: {len(rncs_list)}")
            print(f"Total de R.Os encontradas: {len(ros_list)}")
            print(f"Total de Garantias encontradas: {len(garantias_list)}")
            print(f"Total combinado: {len(combined_list)}")
            print(f"======================================\n")
            
            # Agrupar por setor (apenas para os tipos solicitados)
            ro_por_setor = {}
            rnc_por_setor = {}
            garantias_por_setor = {}

            if tipo_registro_filter in ['ambos', 'ro', 'todos']:
                for item in ros_list:
                    setor = normalizar_setor(item.get('setor_ordem', 'Não informado'))
                    if setor not in ro_por_setor:
                        ro_por_setor[setor] = []
                    ro_por_setor[setor].append(item)

            if tipo_registro_filter in ['ambos', 'rnc', 'todos']:
                for item in rncs_list:
                    setor = normalizar_setor(item.get('setor_ordem', 'Não informado'))
                    if setor not in rnc_por_setor:
                        rnc_por_setor[setor] = []
                    rnc_por_setor[setor].append(item)

            if tipo_registro_filter in ['ambos', 'garantias', 'todos']:
                for item in garantias_list:
                    setor = normalizar_setor(item.get('setor_ordem', 'Não informado'))
                    if setor not in garantias_por_setor:
                        garantias_por_setor[setor] = []
                    garantias_por_setor[setor].append(item)

            return_db_connection(conn)

            # DEBUG detalhado
            print(f"\n=== DEBUG RENDER TEMPLATE ===")
            print(f"tipo_registro_filter: {tipo_registro_filter}")
            print(f"len(rncs_list): {len(rncs_list)}")
            print(f"len(ros_list): {len(ros_list)}")
            print(f"len(garantias_list): {len(garantias_list)}")
            print(f"rnc_por_setor keys: {list(rnc_por_setor.keys()) if rnc_por_setor else 'VAZIO'}")
            print(f"ro_por_setor keys: {list(ro_por_setor.keys()) if ro_por_setor else 'VAZIO'}")
            print(f"garantias_por_setor keys: {list(garantias_por_setor.keys()) if garantias_por_setor else 'VAZIO'}")
            print(f"================================\n")

            return render_template(template, 
                                 rncs_list=combined_list,
                                 rncs=combined_list,
                                 ro_por_setor=ro_por_setor,
                                 rnc_por_setor=rnc_por_setor,
                                 garantias_por_setor=garantias_por_setor,
                                 stats=stats,
                                 start_date=start_date,
                                 end_date=end_date,
                                 report_type=report_type,
                                 tipo_registro_filter=tipo_registro_filter,
                                 setor_filter=setor_filter,
                                 generated_at=datetime.now())
        
        else:
            return "Tipo de relatório não reconhecido", 400
        
        cursor.execute(query, (start_date, end_date))
        rncs = cursor.fetchall()
        
        # Obter colunas
        columns = [desc[0] for desc in cursor.description]
        rncs_list = [dict(zip(columns, rnc)) for rnc in rncs]
        
        # DEBUG: Imprimir informações sobre a consulta
        print(f"\n=== DEBUG RELATÓRIO ===")
        print(f"Tipo: {report_type}")
        print(f"Período: {start_date} a {end_date}")
        print(f"Query executada: {query[:200]}...")
        print(f"Total de RNCs encontradas: {len(rncs_list)}")
        if rncs_list:
            print(f"Primeira RNC: {rncs_list[0]}")
            # DEBUG: Ver valores do campo price
            print(f"\n=== DEBUG PREÇOS ===")
            for i, rnc in enumerate(rncs_list[:5]):  # Primeiras 5 RNCs
                print(f"RNC {rnc.get('rnc_number', 'N/A')}: price='{rnc.get('price')}' (tipo: {type(rnc.get('price'))})")
            print(f"====================\n")
        print(f"Stats calculadas: {stats}")
        print(f"======================\n")
        
        return_db_connection(conn)
        
        # Log de auditoria - geração de relatório
        try:
            from services.audit import log_event
            log_event('REPORT_GENERATE', f'Relatório {report_type} gerado ({start_date} a {end_date})',
                      target_type='REPORT', details=f'{len(rncs_list)} RNCs',
                      user_id=session.get('user_id'), user_name=session.get('user_name'),
                      ip_address=request.remote_addr)
        except Exception:
            pass
        
        # Renderizar template do relatório
        return render_template(template, 
                             rncs_list=rncs_list,
                             rncs=rncs_list,
                             stats=stats,
                             start_date=start_date,
                             end_date=end_date,
                             report_type=report_type,
                             generated_at=datetime.now())
                             
    except Exception as e:
        return f"Erro ao gerar relatório: {str(e)}", 500

def calculate_report_stats(cursor, start_date, end_date):
    """Calcula estatísticas para o relatório"""
    stats = {}
    
    # Total de RNCs
    cursor.execute("""
        SELECT COUNT(*) FROM rncs 
        WHERE is_deleted = 0 AND DATE(created_at) BETWEEN ? AND ?
    """, (start_date, end_date))
    stats['total_rncs'] = cursor.fetchone()[0]
    
    # RNCs por status
    cursor.execute("""
        SELECT status, COUNT(*) FROM rncs 
        WHERE is_deleted = 0 AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY status
    """, (start_date, end_date))
    stats['by_status'] = dict(cursor.fetchall())
    
    # RNCs por prioridade
    cursor.execute("""
        SELECT priority, COUNT(*) FROM rncs 
        WHERE is_deleted = 0 AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY priority
    """, (start_date, end_date))
    stats['by_priority'] = dict(cursor.fetchall())
    
    # RNCs por departamento
    # CORRIGIDO: Usar area_responsavel da RNC, não u.department do usuário
    cursor.execute("""
        SELECT 
            CASE 
                WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' THEN r.area_responsavel
                WHEN r.setor IS NOT NULL AND r.setor != '' THEN r.setor
                ELSE 'Não informado'
            END as departamento,
            COUNT(*) 
        FROM rncs r
        WHERE r.is_deleted = 0 AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
        GROUP BY departamento
    """, (start_date, end_date))
    stats['by_department'] = dict(cursor.fetchall())
    
    # RNCs finalizados vs pendentes
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN status = 'Finalizado' THEN 1 ELSE 0 END) as finalized,
            SUM(CASE WHEN status != 'Finalizado' THEN 1 ELSE 0 END) as pending
        FROM rncs 
        WHERE is_deleted = 0 AND DATE(created_at) BETWEEN ? AND ?
    """, (start_date, end_date))
    result = cursor.fetchone()
    stats['finalized'] = result[0] or 0
    stats['pending'] = result[1] or 0
    
    # Taxa de resolução
    if stats['total_rncs'] > 0:
        stats['resolution_rate'] = round((stats['finalized'] / stats['total_rncs']) * 100, 1)
    else:
        stats['resolution_rate'] = 0
    
    return stats

def calculate_finalized_stats_period(cursor, start_date, end_date):
    """Calcula estatísticas dos RNCs finalizados em um período específico"""
    stats = {}
    
    # Total de RNCs finalizados no período (excluindo departamentos específicos)
    # CORRIGIDO: Usar created_at porque finalized_at está NULL
    cursor.execute("""
        SELECT COUNT(*) FROM rncs 
        WHERE is_deleted = 0 AND status = 'Finalizado'
        AND COALESCE(area_responsavel, setor, '') NOT IN ('Não Definidos', 'Transporte', 'Filial', 'Usinagem plana')
        AND DATE(created_at) BETWEEN ? AND ?
    """, (start_date, end_date))
    stats['total_finalized'] = cursor.fetchone()[0]
    
    # RNCs finalizados por departamento no período
    # CORRIGIDO: Usar area_responsavel da RNC, não u.department do usuário
    cursor.execute("""
        SELECT 
            CASE 
                WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' THEN r.area_responsavel
                WHEN r.setor IS NOT NULL AND r.setor != '' THEN r.setor
                ELSE 'Não informado'
            END as departamento,
            COUNT(*) 
        FROM rncs r
        WHERE r.is_deleted = 0 AND r.status = 'Finalizado'
        AND COALESCE(r.area_responsavel, r.setor, '') NOT IN ('Não Definidos', 'Transporte', 'Filial', 'Usinagem plana')
        AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
        GROUP BY departamento
    """, (start_date, end_date))
    stats['by_department'] = dict(cursor.fetchall())
    
    # RNCs finalizados por prioridade no período
    cursor.execute("""
        SELECT priority, COUNT(*) FROM rncs 
        WHERE is_deleted = 0 AND status = 'Finalizado'
        AND COALESCE(area_responsavel, setor, '') NOT IN ('Não Definidos', 'Transporte', 'Filial', 'Usinagem plana')
        AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY priority
    """, (start_date, end_date))
    stats['by_priority'] = dict(cursor.fetchall())
    
    # Valor total dos RNCs finalizados no período - detecta formato
    cursor.execute("""
        SELECT SUM(
            CASE 
                WHEN price IS NULL OR TRIM(price) = '' OR price = '0' THEN 0
                WHEN price LIKE '%,%' THEN 
                    CAST(
                        REPLACE(
                            REPLACE(
                                REPLACE(TRIM(price), 'R$', ''),
                                '.', ''
                            ),
                            ',', '.'
                        ) AS REAL
                    )
                ELSE 
                    CAST(REPLACE(TRIM(price), 'R$', '') AS REAL)
            END
        ) as total_value
        FROM rncs 
        WHERE is_deleted = 0 AND status = 'Finalizado'
        AND COALESCE(area_responsavel, setor, '') NOT IN ('Não Definidos', 'Transporte', 'Filial', 'Usinagem plana')
        AND DATE(created_at) BETWEEN ? AND ?
    """, (start_date, end_date))
    result = cursor.fetchone()
    stats['total_value'] = result[0] if result[0] else 0
    
    return stats

def calculate_total_stats_period(cursor, start_date, end_date):
    """Calcula estatísticas para relatório total detalhado - com filtros de status e responsável"""
    stats = {}
    
    # Filtro base igual ao relatório por operador
    base_filter = """
        is_deleted = 0 
        AND status IN ('Finalizado', 'Pendente')
        AND (responsavel IS NOT NULL OR causador_user_id IS NOT NULL)
        AND (responsavel != '' OR causador_user_id IS NOT NULL)
        AND CASE
            WHEN created_at LIKE '__/__/____' THEN 
                substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
            ELSE 
                DATE(created_at)
        END BETWEEN ? AND ?
    """
    
    # Total de RNCs no período
    cursor.execute(f"""
        SELECT COUNT(*) FROM rncs 
        WHERE {base_filter}
    """, (start_date, end_date))
    stats['total_rncs'] = cursor.fetchone()[0]
    
    # RNCs por status
    cursor.execute(f"""
        SELECT status, COUNT(*) FROM rncs 
        WHERE {base_filter}
        GROUP BY status
    """, (start_date, end_date))
    stats['by_status'] = dict(cursor.fetchall())
    
    # RNCs por prioridade
    cursor.execute(f"""
        SELECT priority, COUNT(*) FROM rncs 
        WHERE {base_filter}
        GROUP BY priority
    """, (start_date, end_date))
    stats['by_priority'] = dict(cursor.fetchall())
    
    # RNCs por departamento
    cursor.execute("""
        SELECT 
            COALESCE(
                g.name,
                CASE 
                    WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' 
                        AND NOT (r.area_responsavel GLOB '[0-9]*')
                    THEN r.area_responsavel
                    ELSE NULL
                END,
                CASE 
                    WHEN r.setor IS NOT NULL AND r.setor != '' 
                        AND NOT (r.setor GLOB '[0-9]*')
                    THEN r.setor
                    ELSE NULL
                END,
                'Outros'
            ) as departamento,
            COUNT(*) 
        FROM rncs r
        LEFT JOIN groups g ON (
            r.area_responsavel IS NOT NULL 
            AND r.area_responsavel GLOB '[0-9]*'
            AND CAST(r.area_responsavel AS INTEGER) = g.id
        )
        WHERE r.is_deleted = 0 
        AND r.status IN ('Finalizado', 'Pendente')
        AND (r.responsavel IS NOT NULL OR r.causador_user_id IS NOT NULL)
        AND (r.responsavel != '' OR r.causador_user_id IS NOT NULL)
        AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
        GROUP BY departamento
    """, (start_date, end_date))
    stats['by_department'] = dict(cursor.fetchall())
    
    # Valor total - detecta formato pelo conteúdo (vírgula = brasileiro, ponto = decimal)
    cursor.execute("""
        SELECT SUM(
            CASE 
                WHEN price IS NULL OR TRIM(price) = '' OR price = '0' THEN 0
                WHEN price LIKE '%,%' THEN 
                    CAST(
                        REPLACE(
                            REPLACE(
                                REPLACE(TRIM(price), 'R$', ''),
                                '.', ''
                            ),
                            ',', '.'
                        ) AS REAL
                    )
                ELSE 
                    CAST(REPLACE(TRIM(price), 'R$', '') AS REAL)
            END
        ) as total_value
        FROM rncs 
        WHERE is_deleted = 0 
        AND status IN ('Finalizado', 'Pendente')
        AND (responsavel IS NOT NULL OR causador_user_id IS NOT NULL)
        AND (responsavel != '' OR causador_user_id IS NOT NULL)
        AND CASE
            WHEN created_at LIKE '__/__/____' THEN 
                substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
            ELSE 
                DATE(created_at)
        END BETWEEN ? AND ?
    """, (start_date, end_date))
    result = cursor.fetchone()
    stats['total_value'] = result[0] if result[0] else 0
    
    return stats

def calculate_operator_stats_period(cursor, start_date, end_date, status_filter='both'):
    """Calcula estatísticas para relatório por operador"""
    stats = {}
    
    # Definir filtro de status
    if status_filter == 'finalized':
        status_clause = "AND status = 'Finalizado'"
    elif status_filter == 'pending':
        status_clause = "AND status = 'Pendente'"
    else:  # both
        status_clause = "AND status IN ('Finalizado', 'Pendente')"
    
    # Total de RNCs no período
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM rncs r
        LEFT JOIN groups g ON (
            CAST(r.area_responsavel AS TEXT) = CAST(g.id AS TEXT) OR
            CAST(r.setor AS TEXT) = CAST(g.id AS TEXT)
        )
        WHERE r.is_deleted = 0 
        {status_clause}
        AND CASE
            WHEN g.name IS NOT NULL THEN g.name
            ELSE COALESCE(r.area_responsavel, r.setor, '')
        END NOT IN ('Não Definidos', 'Transporte', 'Filial', 'Usinagem plana')
        AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
    """, (start_date, end_date))
    stats['total_rncs'] = cursor.fetchone()[0]
    
    # RNCs por operador
    cursor.execute(f"""
        SELECT 
            COALESCE(causador_u.name, u.name, r.responsavel) as operador,
            COUNT(*) 
        FROM rncs r
        LEFT JOIN groups g ON (
            CAST(r.area_responsavel AS TEXT) = CAST(g.id AS TEXT) OR
            CAST(r.setor AS TEXT) = CAST(g.id AS TEXT)
        )
        LEFT JOIN users u ON CAST(r.responsavel AS TEXT) = CAST(u.id AS TEXT)
        LEFT JOIN users causador_u ON r.causador_user_id = causador_u.id
        WHERE r.is_deleted = 0 
        {status_clause}
        AND (r.responsavel IS NOT NULL OR r.causador_user_id IS NOT NULL)
        AND (r.responsavel != '' OR r.causador_user_id IS NOT NULL)
        AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
        GROUP BY operador
        ORDER BY 2 DESC
    """, (start_date, end_date))
    stats['by_operator'] = dict(cursor.fetchall())

    # Valor por operador - detecta formato pelo conteúdo
    cursor.execute(f"""
        SELECT 
            COALESCE(causador_u.name, u.name, r.responsavel) as operador,
            SUM(
                CASE 
                    WHEN r.price IS NULL OR TRIM(r.price) = '' OR r.price = '0' THEN 0
                    WHEN r.price LIKE '%,%' THEN 
                        CAST(
                            REPLACE(
                                REPLACE(
                                    REPLACE(TRIM(r.price), 'R$', ''),
                                    '.', ''
                                ),
                                ',', '.'
                            ) AS REAL
                        )
                    ELSE 
                        CAST(REPLACE(TRIM(r.price), 'R$', '') AS REAL)
                END
            )
        FROM rncs r
        LEFT JOIN groups g ON (
            CAST(r.area_responsavel AS TEXT) = CAST(g.id AS TEXT) OR
            CAST(r.setor AS TEXT) = CAST(g.id AS TEXT)
        )
        LEFT JOIN users u ON CAST(r.responsavel AS TEXT) = CAST(u.id AS TEXT)
        LEFT JOIN users causador_u ON r.causador_user_id = causador_u.id
        WHERE r.is_deleted = 0 
        {status_clause}
        AND (r.responsavel IS NOT NULL OR r.causador_user_id IS NOT NULL)
        AND (r.responsavel != '' OR r.causador_user_id IS NOT NULL)
        AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
        GROUP BY operador
        ORDER BY 2 DESC
    """, (start_date, end_date))
    stats['value_by_operator'] = dict(cursor.fetchall())
    
    return stats

def calculate_sector_stats_period(cursor, start_date, end_date):
    """Calcula estatísticas para relatório por setor - com filtros de status e responsável"""
    stats = {}
    
    # Filtro base igual ao relatório por operador
    base_filter = """
        r.is_deleted = 0 
        AND r.status IN ('Finalizado', 'Pendente')
        AND (r.responsavel IS NOT NULL OR r.causador_user_id IS NOT NULL)
        AND (r.responsavel != '' OR r.causador_user_id IS NOT NULL)
        AND CASE
            WHEN r.created_at LIKE '__/__/____' THEN 
                substr(r.created_at, 7, 4) || '-' || substr(r.created_at, 4, 2) || '-' || substr(r.created_at, 1, 2)
            ELSE 
                DATE(r.created_at)
        END BETWEEN ? AND ?
    """
    
    # Total de RNCs no período
    cursor.execute(f"""
        SELECT COUNT(*) FROM rncs r
        WHERE {base_filter}
    """, (start_date, end_date))
    stats['total_rncs'] = cursor.fetchone()[0]
    
    # RNCs por setor (resolvendo IDs numéricos via JOIN com groups)
    dept_case = """
        COALESCE(
            g.name,
            CASE 
                WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' 
                    AND NOT (r.area_responsavel GLOB '[0-9]*')
                THEN r.area_responsavel
                ELSE NULL
            END,
            CASE 
                WHEN r.setor IS NOT NULL AND r.setor != '' 
                    AND NOT (r.setor GLOB '[0-9]*')
                THEN r.setor
                ELSE NULL
            END,
            'Outros'
        )
    """
    cursor.execute(f"""
        SELECT {dept_case} as departamento, COUNT(*) FROM rncs r
        LEFT JOIN groups g ON (
            r.area_responsavel IS NOT NULL 
            AND r.area_responsavel GLOB '[0-9]*'
            AND CAST(r.area_responsavel AS INTEGER) = g.id
        )
        WHERE {base_filter}
        GROUP BY departamento
        ORDER BY COUNT(*) DESC
    """, (start_date, end_date))
    stats['by_sector'] = dict(cursor.fetchall())
    
    # Valor por setor - detecta formato pelo conteúdo
    cursor.execute(f"""
        SELECT {dept_case} as departamento, 
               SUM(
                   CASE 
                       WHEN r.price LIKE '%,%' THEN 
                           CAST(REPLACE(REPLACE(REPLACE(TRIM(r.price), 'R$', ''), '.', ''), ',', '.') AS REAL)
                       ELSE 
                           CAST(REPLACE(TRIM(r.price), 'R$', '') AS REAL)
                   END
               )
        FROM rncs r
        LEFT JOIN groups g ON (
            r.area_responsavel IS NOT NULL 
            AND r.area_responsavel GLOB '[0-9]*'
            AND CAST(r.area_responsavel AS INTEGER) = g.id
        )
        WHERE {base_filter}
          AND r.price IS NOT NULL AND r.price != '' AND r.price NOT IN ('0','0.0')
        GROUP BY departamento
        ORDER BY 2 DESC
    """, (start_date, end_date))
    stats['value_by_sector'] = dict(cursor.fetchall())
    
    # RNCs por status por setor
    cursor.execute(f"""
        SELECT {dept_case} as departamento, r.status, COUNT(*) FROM rncs r
        LEFT JOIN groups g ON (
            r.area_responsavel IS NOT NULL 
            AND r.area_responsavel GLOB '[0-9]*'
            AND CAST(r.area_responsavel AS INTEGER) = g.id
        )
        WHERE {base_filter}
        GROUP BY departamento, r.status
    """, (start_date, end_date))
    sector_status = cursor.fetchall()
    stats['sector_status'] = {}
    for dept, status, count in sector_status:
        if dept not in stats['sector_status']:
            stats['sector_status'][dept] = {}
        stats['sector_status'][dept][status] = count
    
    return stats

def calculate_finalized_stats(cursor):
    """Calcula estatísticas dos RNCs finalizados (todos)"""
    stats = {}
    
    # Total de RNCs finalizados
    cursor.execute("""
        SELECT COUNT(*) FROM rncs 
        WHERE is_deleted = 0 AND status = 'Finalizado'
    """)
    stats['total_finalized'] = cursor.fetchone()[0]
    
    # RNCs finalizados por departamento (usar campos da própria RNC)
    cursor.execute("""
        SELECT 
            CASE 
                WHEN r.area_responsavel IS NOT NULL AND r.area_responsavel != '' THEN r.area_responsavel
                WHEN r.setor IS NOT NULL AND r.setor != '' THEN r.setor
                ELSE 'Não informado'
            END as departamento,
            COUNT(*)
        FROM rncs r
        WHERE r.is_deleted = 0 AND r.status = 'Finalizado'
        GROUP BY departamento
    """)
    stats['by_department'] = dict(cursor.fetchall())
    
    # RNCs finalizados por prioridade
    cursor.execute("""
        SELECT priority, COUNT(*) FROM rncs 
        WHERE is_deleted = 0 AND status = 'Finalizado'
        GROUP BY priority
    """)
    stats['by_priority'] = dict(cursor.fetchall())
    
    # RNCs finalizados por mês (últimos 12 meses)
    cursor.execute("""
        SELECT strftime('%Y-%m', finalized_at) as month, COUNT(*) 
        FROM rncs 
        WHERE is_deleted = 0 AND status = 'Finalizado'
        AND finalized_at >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', finalized_at)
        ORDER BY month DESC
    """)
    stats['by_month'] = dict(cursor.fetchall())
    
    # Valor total dos RNCs finalizados
    # CORRIGIDO: Remover 'R$', espaços, vírgulas e aspas do price antes de fazer o CAST
    cursor.execute("""
        SELECT SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', ''), '"', ''), '''', '') AS REAL)) FROM rncs 
        WHERE is_deleted = 0 AND status = 'Finalizado'
        AND price IS NOT NULL AND price != '' AND price != '0' AND price != '0.0'
    """)
    result = cursor.fetchone()
    stats['total_value'] = result[0] if result[0] else 0
    
    return stats
