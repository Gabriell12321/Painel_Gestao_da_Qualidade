from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
import uuid
from datetime import datetime

# Importar blueprint de field_locks
from routes.field_locks import field_locks_bp

app = Flask(__name__)
CORS(app)  # Permite requisições do frontend

# Registrar blueprints
app.register_blueprint(field_locks_bp)

# Rota de teste para verificar se o blueprint está funcionando
@app.route('/test-blueprint')
def test_blueprint():
    return jsonify({'message': 'Blueprint field_locks funcionando!', 'routes': [rule.rule for rule in app.url_map.iter_rules()]})

# Configurações de E-mail (ler de variáveis de ambiente quando disponível)
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),  # Para Outlook: use 'smtp-mail.outlook.com'
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'email': os.getenv('SMTP_USER', ''),
    'password': os.getenv('SMTP_PASS', '')
}

# Para Outlook/Hotmail, descomente as linhas abaixo:
# EMAIL_CONFIG = {
#     'smtp_server': 'smtp-mail.outlook.com',
#     'smtp_port': 587,
#     'email': 'seu-email@outlook.com',
#     'password': 'sua-senha-normal'
# }

# Permitir requisições do frontend (CORS)
# Já está incluso: CORS(app)
# Se quiser permitir apenas de um domínio específico, use:
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


def send_email(recipient_email, subject, content, email_type):
    """Função para enviar e-mail"""
    try:
        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg['Reply-To'] = EMAIL_CONFIG['email']
        # Usar UUID para Message-ID
        msg['Message-ID'] = f"<{uuid.uuid4()}@{EMAIL_CONFIG['email']}>"

        # Versão texto simples
        text_content = content

        # Versão HTML formatada
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .report-box {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #dc2626; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
                pre {{ font-family: 'Courier New', monospace; white-space: pre-wrap; margin: 0; color: #374151; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin: 0;">IPPEL - Relatório RNC</h1>
            </div>
            <div class="content">
                <div class="info-box">
                    <h2 style="color: #dc2626; margin-top: 0;">Relatório de Não Conformidade Interna - RNC</h2>
                    <p style="color: #6b7280; font-size: 14px;">
                        <strong>Tipo de Relatório:</strong> {email_type}<br>
                        <strong>Data de Envio:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </p>
                </div>
                <div class="report-box">
                    <pre>{content}</pre>
                </div>
                <div class="footer">
                    <p>Este e-mail foi enviado automaticamente pelo sistema RNC da IPPEL.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Anexar conteúdo
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))



        # Conectar ao servidor SMTP
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])

        # Enviar e-mail
        server.send_message(msg)
        server.quit()

        return True, "E-mail enviado com sucesso!"

    except Exception as e:
        return False, f"Erro ao enviar e-mail: {str(e)}"

@app.route('/')
def home():
    """Rota principal - serve o arquivo HTML"""
    return send_file('index.html')

@app.route('/status')
def status():
    """Rota para verificar status do servidor"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'message': 'Servidor RNC funcionando corretamente'
    })

@app.route('/send-email', methods=['POST'])
def send_email_route():
    """Rota para enviar e-mail"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['recipientEmail', 'subject', 'content', 'emailType']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório não fornecido: {field}'
                }), 400

        # Extrair dados
        recipient_email = data['recipientEmail']
        subject = data['subject']
        content = data['content']
        email_type = data['emailType']

        # Enviar e-mail
        success, message = send_email(recipient_email, subject, content, email_type)

        if success:
            # Log do e-mail enviado
            log_data = {
                'to': recipient_email,
                'subject': subject,
                'type': email_type,
                'timestamp': datetime.now().isoformat()
                # Removido campo duplicado 'timestamp' para corrigir o erro de sintaxe
                
            }
            print(f"✅ E-mail enviado: {log_data}")
            
            return jsonify({
                'success': True,
                'message': message,
                'messageId': f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500

    except Exception as e:
        print(f"❌ Erro no servidor: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro interno do servidor: {str(e)}'
        }), 500

@app.route('/test-email')
def test_email():
    """Rota para testar configuração de e-mail"""
    try:
        # Testar conexão SMTP
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.quit()
        
        return jsonify({
            'success': True,
            'message': 'Configuração de e-mail está correta!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro na configuração de e-mail: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Iniciando servidor RNC...")
    print("📧 Sistema de e-mail configurado")
    print("📄 Acesse: http://localhost:5000")
    print("🔧 Para testar e-mail: http://localhost:5000/test-email")
    print()
    
    # Verificar configuração de e-mail
    if EMAIL_CONFIG['email'] == 'seu-email@gmail.com':
        print("⚠️  ATENÇÃO: Configure suas credenciais de e-mail no arquivo server.py")
        print("   - Linha 12: EMAIL_CONFIG['email']")
        print("   - Linha 13: EMAIL_CONFIG['password']")
        print()
    
    app.run(host='0.0.0.0', port=5000, debug=True) 