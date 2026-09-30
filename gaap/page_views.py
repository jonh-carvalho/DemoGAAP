import json
from datetime import datetime
from urllib import error, request as urllib_request

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import SolicitacaoExperimentalForm


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

    req = urllib_request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=10) as response:
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
    if request.method == 'POST':
        form = SolicitacaoExperimentalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Recebemos sua solicitação. Nossa equipe entrará em contato para conversar sobre a aula experimental.',
            )
            return redirect('home')
    else:
        form = SolicitacaoExperimentalForm()

    return render(request, 'gaap/home.html', {'form': form})


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

    if request.method == 'POST':
        action = request.POST.get('action')
        appointment_id = request.POST.get('agendamento_id')
        if action == 'cancel' and appointment_id:
            status_code, result = _api_call(
                'PATCH', f'agendamentos/{appointment_id}/', {'status': 'CANCELADO'}, request=request
            )
            _notify_api_result(request, status_code, result, 'Agendamento cancelado.')
            return redirect('agendamentos_page')

        payload = {
            'aluno_id': request.POST.get('aluno_id'),
            'servico_id': request.POST.get('servico_id'),
            'profissional_id': request.POST.get('profissional_id'),
            'inicio': request.POST.get('inicio'),
            'fim': request.POST.get('fim'),
            'status': request.POST.get('status', 'PENDENTE'),
            'observacoes': request.POST.get('observacoes', '').strip(),
        }
        if not all(payload[key] for key in ('aluno_id', 'servico_id', 'profissional_id', 'inicio', 'fim')):
            messages.error(request, 'Preencha aluno, serviço, profissional e horário.')
            request.session['appointment_form'] = payload
            request.session['appointment_form_id'] = appointment_id if action == 'update' else ''
            return redirect(f"/agendamentos/?{'editar=' + appointment_id if action == 'update' and appointment_id else 'novo=1'}")

        if action == 'update' and appointment_id:
            method = 'PATCH'
            endpoint = f'agendamentos/{appointment_id}/'
            success_message = 'Agendamento atualizado.'
        else:
            method = 'POST'
            endpoint = 'agendamentos/'
            success_message = 'Agendamento criado.'
        status_code, result = _api_call(method, endpoint, payload, request=request)
        succeeded = _notify_api_result(request, status_code, result, success_message)
        if succeeded:
            request.session.pop('appointment_form', None)
            request.session.pop('appointment_form_id', None)
        else:
            request.session['appointment_form'] = payload
            request.session['appointment_form_id'] = appointment_id if action == 'update' else ''
            return_to_form = f"?editar={appointment_id}" if action == 'update' and appointment_id else '?novo=1'
            return redirect(f'/agendamentos/{return_to_form}')
        return redirect('agendamentos_page')

    restored_form = request.session.pop('appointment_form', None)
    restored_form_id = request.session.pop('appointment_form_id', '')
    all_items = _fetch_json(request, 'agendamentos/')
    status_labels = {
        'PENDENTE': 'Pendente',
        'CONFIRMADO': 'Confirmado',
        'CANCELADO': 'Cancelado',
        'REALIZADO': 'Realizado',
    }
    for item in all_items:
        item['status_label'] = status_labels.get(item.get('status'), item.get('status', '-'))
        item['inicio_display'] = _format_datetime(item.get('inicio'))
        item['fim_display'] = _format_datetime(item.get('fim'))

    selected = None
    edit_id = request.GET.get('editar') or restored_form_id
    if edit_id:
        selected = next((item for item in all_items if str(item.get('id')) == edit_id), None)

    filters = {
        'q': request.GET.get('q', '').strip(),
        'data': request.GET.get('data', ''),
        'status': request.GET.get('status', ''),
        'servico': request.GET.get('servico', ''),
        'profissional': request.GET.get('profissional', ''),
    }
    items = all_items
    if filters['q']:
        term = filters['q'].casefold()
        items = [
            item for item in items
            if term in item.get('aluno', {}).get('nome', '').casefold()
            or term in item.get('servico', {}).get('nome', '').casefold()
            or term in item.get('profissional', {}).get('nome', '').casefold()
        ]
    if filters['data']:
        items = [item for item in items if (item.get('inicio') or '').startswith(filters['data'])]
    if filters['status']:
        items = [item for item in items if item.get('status') == filters['status']]
    if filters['servico']:
        items = [item for item in items if str(item.get('servico', {}).get('id')) == filters['servico']]
    if filters['profissional']:
        items = [item for item in items if str(item.get('profissional', {}).get('id')) == filters['profissional']]

    form_values = {
        'id': selected.get('id', '') if selected else '',
        'aluno_id': selected.get('aluno', {}).get('id', '') if selected else '',
        'servico_id': selected.get('servico', {}).get('id', '') if selected else '',
        'profissional_id': selected.get('profissional', {}).get('id', '') if selected else '',
        'inicio': _format_datetime(selected.get('inicio'), input_format=True) if selected else '',
        'fim': _format_datetime(selected.get('fim'), input_format=True) if selected else '',
        'status': selected.get('status', 'PENDENTE') if selected else 'PENDENTE',
        'observacoes': selected.get('observacoes', '') if selected else '',
    }
    if restored_form:
        form_values.update(restored_form)
        form_values['id'] = edit_id or ''
    context = {
        'items': items,
        'total_count': len(all_items),
        'pending_count': sum(item.get('status') == 'PENDENTE' for item in all_items),
        'confirmed_count': sum(item.get('status') == 'CONFIRMADO' for item in all_items),
        'canceled_count': sum(item.get('status') == 'CANCELADO' for item in all_items),
        'alunos': _fetch_json(request, 'alunos/'),
        'servicos': _fetch_json(request, 'servicos/'),
        'profissionais': _fetch_json(request, 'profissionais/'),
        'filters': filters,
        'form_values': form_values,
        'show_form': bool(request.GET.get('novo') or selected or restored_form),
        'is_editing': bool(selected),
    }
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


def _notify_api_result(request, status_code, result, success_message):
    if status_code in {200, 201, 204}:
        messages.success(request, success_message)
        return True
    if isinstance(result, dict):
        details = []
        for value in result.values():
            details.extend(value if isinstance(value, list) else [str(value)])
        message = ' '.join(str(detail) for detail in details if detail)
    else:
        message = str(result)
    messages.error(request, message or 'Não foi possível salvar o agendamento.')
    return False


def _format_datetime(value, input_format=False):
    if not value:
        return ''
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if timezone.is_aware(parsed):
            parsed = timezone.localtime(parsed)
        return parsed.strftime('%Y-%m-%dT%H:%M' if input_format else '%d/%m/%Y %H:%M')
    except (TypeError, ValueError):
        return value
