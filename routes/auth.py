from flask import Blueprint, request, jsonify, session, g
from werkzeug.security import check_password_hash
import logging

from services.users import get_user_by_email
try:
    # Progressive lockout service (dynamic import to avoid analysis issues)
    import importlib as _importlib
    _lockout = _importlib.import_module('services.lockout')
    is_locked = getattr(_lockout, 'is_locked')
    record_failure = getattr(_lockout, 'record_failure')
    reset_success = getattr(_lockout, 'reset_success')
except Exception:
    def is_locked(_uid: int): return (False, 0)  # type: ignore
    def record_failure(_uid: int, ip: str | None = None): return (0, None)  # type: ignore
    def reset_success(_uid: int): return None  # type: ignore
try:
    import importlib
    _rl = importlib.import_module('services.rate_limit')
    rate_limit = getattr(_rl, 'rate_limit')
except Exception:
    # fallback no-op
    def rate_limit(_x):
        def _dec(f):
            return f
        return _dec

auth = Blueprint('auth_bp', __name__)
logger = logging.getLogger('ippel.auth')

@auth.post('/api/login')
@rate_limit("5 per minute; 20 per hour")
def login():
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        user_data = get_user_by_email(email)
        # If we can resolve a user, enforce progressive lockout check before password verification
        if user_data:
            uid = user_data[0]
            locked, seconds = is_locked(uid)
            if locked:
                # Log lockout event
                try:
                    import importlib
                    _sl = importlib.import_module('services.security_log')
                    _sl.sec_log('auth', 'lockout', ip=request.remote_addr, user_id=uid, email=email, status='blocked', details={'seconds_remaining': seconds})
                except Exception:
                    pass
                return jsonify({'success': False, 'message': f'Conta temporariamente bloqueada. Tente novamente em {seconds} segundos.'}), 429
        if user_data and check_password_hash(user_data[3], password):
            # Support both session and JWT during migration: set session AND return tokens
            session['user_id'] = user_data[0]
            session['user_name'] = user_data[1]
            session['user_email'] = user_data[2]
            session['user_department'] = user_data[4]
            session['user_role'] = user_data[5]
            session.permanent = True
            # Reset lockout state on successful auth
            try:
                reset_success(user_data[0])
            except Exception:
                pass
            # Issue JWT access/refresh
            try:
                import importlib
                _jwt = importlib.import_module('services.jwt_auth')
                access, access_exp = _jwt.create_access_token(user_data)
                refresh, refresh_exp, jti = _jwt.create_refresh_token(
                    user_data,
                    user_agent=request.headers.get('User-Agent'),
                    ip=request.remote_addr,
                )
            except Exception:
                access, access_exp, refresh, refresh_exp = None, None, None, None

            resp = jsonify({
                'success': True,
                'message': 'Login realizado com sucesso!',
                'redirect': '/dashboard',
                'user': {
                    'name': user_data[1],
                    'email': user_data[2],
                    'department': user_data[4]
                },
                'tokens': {
                    'access': access,
                    'access_expires': access_exp,
                    'refresh': refresh,
                    'refresh_expires': refresh_exp,
                }
            })
            try:
                resp.set_cookie('IPPEL_UID', str(user_data[0]), max_age=60*60*8, path='/', httponly=False, samesite='Lax')
            except Exception:
                pass
            # Log sucesso de login
            try:
                import importlib
                _sl = importlib.import_module('services.security_log')
                _sl.sec_log('auth', 'login', ip=request.remote_addr, user_id=user_data[0], email=email, status='success')
            except Exception:
                pass
            # Log de auditoria
            try:
                from services.audit import log_login
                log_login(user_data[0], user_data[1], request.remote_addr, request.headers.get('User-Agent'))
            except Exception:
                pass
            return resp
        # Log falha de login e aplicar contagem progressiva (se o usuário existir)
        try:
            import importlib
            _sl = importlib.import_module('services.security_log')
            _sl.sec_log('auth', 'login', ip=request.remote_addr, email=email, status='fail')
        except Exception:
            pass
        try:
            if user_data:
                failed_count, locked_until = record_failure(user_data[0], ip=request.remote_addr)
                if locked_until:
                    # Informar lockout ao cliente
                    now = __import__('time').time()
                    seconds = max(0, int(locked_until - now))
                    return jsonify({'success': False, 'message': f'Conta temporariamente bloqueada após múltiplas tentativas. Tente novamente em {seconds} segundos.'}), 429
        except Exception:
            pass
        return jsonify({'success': False, 'message': 'Email ou senha incorretos'}), 401
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do sistema'}), 500

@auth.get('/api/logout')
def logout():
    try:
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        # Log de auditoria antes de limpar sessão
        try:
            from services.audit import log_logout
            log_logout(user_id, user_name, request.remote_addr)
        except Exception:
            pass
        for k in ['user_id','user_name','user_email','user_department','user_role']:
            try: session.pop(k, None)
            except Exception: pass
        session.clear()
        # Best-effort: if a refresh token JTI is provided, revoke it
        try:
            import importlib
            _jwt = importlib.import_module('services.jwt_auth')
            jti = request.headers.get('X-Refresh-JTI')
            if jti:
                _jwt.revoke_refresh(jti)
        except Exception:
            pass
        resp = jsonify({'success': True, 'message': 'Logout realizado com sucesso!'})
        try: resp.delete_cookie('IPPEL_UID', path='/')
        except Exception: pass
        return resp
    except Exception:
        return jsonify({'success': True})


@auth.post('/api/token/refresh')
@rate_limit("20 per minute")
def token_refresh():
    """Rotate refresh token and return new access + refresh.
    Clients send refresh token in JSON: {refresh: "..."}
    """
    try:
        data = request.get_json(silent=True) or {}
        old_refresh = data.get('refresh')
        if not old_refresh:
            return jsonify({'success': False, 'message': 'Refresh token ausente'}), 400

        import importlib
        _jwt = importlib.import_module('services.jwt_auth')

        def _user_provider(uid: int):
            from services.users import get_user_by_id as _get_user_by_id
            return _get_user_by_id(uid)

        access, access_exp, new_refresh, refresh_exp, uid = _jwt.rotate_refresh(
            old_refresh,
            user_agent=request.headers.get('User-Agent'),
            ip=request.remote_addr,
            user_row_provider=_user_provider,
        )
        return jsonify({
            'success': True,
            'tokens': {
                'access': access,
                'access_expires': access_exp,
                'refresh': new_refresh,
                'refresh_expires': refresh_exp,
            }
        })
    except Exception as e:
        try:
            import importlib
            _sl = importlib.import_module('services.security_log')
            _sl.sec_log('auth', 'token_refresh', ip=request.remote_addr, status='fail', details={'error': str(e)})
        except Exception:
            pass
        return jsonify({'success': False, 'message': 'Refresh inválido'}), 401
