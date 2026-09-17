import json
from urllib import error, request

from django.contrib import messages
from django.shortcuts import redirect, render


API_BASE = 'http://127.0.0.1:8000/api/v1'


def _token_from_session(request):
    return request.session.get('access_token')


def _auth_headers(request):
    token = _token_from_session(request)
    if not token:
        return {}
    return {'Authorization': f'Bearer {token}'}


def _api_call(method, path, data=None, request=None):
    url = f'{API_BASE}/{path.lstrip("/")}'
    headers = {'Content-Type': 'application/json'}
    if request is not None:
        headers.update(_auth_headers(request))

    payload = None
    if data is not None:
        payload = json.dumps(data).encode('utf-8')

    req = request.Request(url, data=payload, headers=headers, method=method)
    try:
        with __import__('urllib.request').request.urlopen(req, timeout=10) as response:
            body = response.read().decode('utf-8')
            return response.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        try:
            body = exc.read().decode('utf-8')
            detail = json.loads(body)
        except Exception:
            detail = {'detail': str(exc)}
        return exc.code, detail
    except Exception:
        return None, {'detail': 'Não foi possível conectar à API do GAAP.'}


def home(request):
    return render(request, 'gaap/home.html')


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            messages.error(request, 'Informe usuário e senha.')
            return render(request, 'gaap/login.html')

        status_code, data = _api_call('POST', 'auth/token/', {'username': username, 'password': password})
        if status_code != 200:
            messages.error(request, data.get('detail', 'Credenciais inválidas.'))
            return render(request, 'gaap/login.html')

        request.session['access_token'] = data.get('access')
        request.session['refresh_token'] = data.get('refresh')
        messages.success(request, 'Login realizado com sucesso.')
        return redirect('dashboard')

    return render(request, 'gaap/login.html')


def dashboard(request):
    token = _token_from_session(request)
    if not token:
        return redirect('login_page')

    context = {
        'usuarios': _fetch_json(request, 'usuarios/'),
        'servicos': _fetch_json(request, 'servicos/'),
        'agendamentos': _fetch_json(request, 'agendamentos/'),
        'relatorios': _fetch_json(request, 'relatorios/'),
    }
    return render(request, 'gaap/dashboard.html', context)


def servicos(request):
    if not _token_from_session(request):
        return redirect('login_page')
    context = {'items': _fetch_json(request, 'servicos/')}
    return render(request, 'gaap/servicos.html', context)


def agendamentos(request):
    if not _token_from_session(request):
        return redirect('login_page')
    context = {'items': _fetch_json(request, 'agendamentos/')}
    return render(request, 'gaap/agendamentos.html', context)


def presencas(request):
    if not _token_from_session(request):
        return redirect('login_page')
    context = {'items': _fetch_json(request, 'relatorios/')}
    return render(request, 'gaap/presencas.html', context)


def _fetch_json(request, endpoint):
    status_code, payload = _api_call('GET', endpoint, request=request)
    if status_code in {401, 403}:
        request.session.flush()
        return []
    if status_code is None:
        return []
    if isinstance(payload, list):
        return payload
    return payload.get('results', [])
