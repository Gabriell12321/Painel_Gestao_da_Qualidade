#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚡ Integração das Melhorias de Segurança no Sistema Principal
Arquivo para integrar todas as melhorias de segurança ao server_form.py
"""

import os
import sys

# Adicionar o diretório atual ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def integrate_security_enhancements():
    """
    Integrar melhorias de segurança ao sistema principal
    """
    
    # Importar módulos de segurança
    try:
        from security_enhancements import SecurityManager, SECURITY_CONFIG, add_security_headers
        from two_factor_auth import TwoFactorAuth
        from security_routes import init_security_routes
        
        print("✅ Módulos de segurança importados com sucesso")
        return True
        
    except ImportError as e:
        print(f"❌ Erro ao importar módulos de segurança: {e}")
        return False

def check_security_dependencies():
    """
    Verificar dependências necessárias para segurança
    """
    required_packages = [
        'pyotp',    # Para 2FA
        'qrcode',   # Para QR codes do 2FA
        'Pillow',   # Para geração de imagens QR
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - Instalado")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - Não encontrado")
    
    if missing_packages:
        print(f"\n📦 Instale os pacotes em falta:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_security_integration_patch():
    """
    Criar patch para integrar segurança no server_form.py
    """
    
    patch_content = '''
# =============================================================================
# 🔐 INTEGRAÇÃO DE SEGURANÇA IPPEL
# Adicionar após as importações existentes no server_form.py
# =============================================================================

# Importar módulos de segurança
try:
    from security_enhancements import SecurityManager, SECURITY_CONFIG, add_security_headers
    from two_factor_auth import TwoFactorAuth
    from security_routes import init_security_routes
    SECURITY_ENABLED = True
    print("🔐 Sistema de segurança avançada carregado")
except ImportError as e:
    print(f"⚠️ Sistema de segurança não disponível: {e}")
    SECURITY_ENABLED = False

# =============================================================================
# CONFIGURAÇÃO DE SEGURANÇA
# Adicionar após a criação da instância Flask (app = Flask(__name__))
# =============================================================================

if SECURITY_ENABLED:
    # Inicializar gerenciador de segurança
    security_manager = SecurityManager(app)
    tfa_system = TwoFactorAuth()
    
    # Inicializar rotas de segurança
    init_security_routes(app)
    
    # Middleware de segurança global
    @app.before_request
    def security_middleware():
        from flask import g, request
        g.security_manager = security_manager
        
        # Log de todas as requisições para auditoria
        if request.endpoint:
            security_manager.log_security_event('REQUEST', {
                'endpoint': request.endpoint,
                'method': request.method,
                'ip_address': security_manager.get_client_ip(),
                'user_agent': request.headers.get('User-Agent', '')[:200]
            })
    
    @app.after_request  
    def add_security_headers_middleware(response):
        return add_security_headers(response)
    
    # Limpeza automática de dados de segurança
    import threading
    import time
    
    def cleanup_security_data():
        while True:
            time.sleep(3600)  # A cada hora
            try:
                security_manager.cleanup_expired_data()
            except Exception as e:
                print(f"Erro na limpeza de segurança: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_security_data, daemon=True)
    cleanup_thread.start()

# =============================================================================
# MODIFICAÇÕES NA ROTA DE LOGIN EXISTENTE
# Substituir o conteúdo da rota /api/login por:
# =============================================================================

@app.route('/api/login', methods=['POST'])
def api_login():
    """Login com segurança aprimorada"""
    if SECURITY_ENABLED:
        # Usar o login seguro
        from security_routes import security_bp
        return security_bp.view_functions['enhanced_login']()
    else:
        # Fallback para login original
        return original_login()

# =============================================================================
# ROTAS DE SEGURANÇA ADICIONAIS  
# Adicionar estas rotas ao arquivo principal
# =============================================================================

@app.route('/security-dashboard')
@require_auth
def security_dashboard():
    """Dashboard de segurança para administradores"""
    if not SECURITY_ENABLED:
        return "Sistema de segurança não disponível", 503
    
    return render_template('security_dashboard.html')

@app.route('/api/security-status')
@require_auth  
def security_status():
    """Status de segurança do usuário"""
    if not SECURITY_ENABLED:
        return jsonify({'security_enabled': False})
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    # Status do 2FA
    tfa_status = tfa_system.get_2fa_status(user_id)
    
    # Sessões ativas
    with sqlite3.connect('ippel_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM active_sessions 
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        active_sessions = cursor.fetchone()[0]
    
    return jsonify({
        'security_enabled': True,
        'two_factor': tfa_status,
        'active_sessions': active_sessions,
        'last_login': session.get('login_time'),
        'session_expires': session.get('login_time', 0) + SECURITY_CONFIG['SESSION_TIMEOUT']
    })

'''
    
    # Salvar patch
    with open('security_integration_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("✅ Patch de integração criado: security_integration_patch.py")

if __name__ == "__main__":
    print("🔐 IPPEL Security Integration")
    print("=" * 50)
    
    # Verificar dependências
    if not check_security_dependencies():
        print("\n❌ Instale as dependências antes de continuar")
        sys.exit(1)
    
    # Testar importações
    if not integrate_security_enhancements():
        print("\n❌ Erro na integração")
        sys.exit(1)
    
    # Criar patch de integração
    create_security_integration_patch()
    
    print("\n🎉 Sistema de segurança pronto!")
    print("\nPróximos passos:")
    print("1. Instalar dependências: pip install pyotp qrcode Pillow")
    print("2. Aplicar o patch ao server_form.py")
    print("3. Reiniciar o servidor")
    print("4. Acessar /security-dashboard para configurações")
