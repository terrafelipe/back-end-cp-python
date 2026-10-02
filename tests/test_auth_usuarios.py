from tests.ajudantes import erro

NOVA_EMPRESA = {
    "empresa": "Loja Nova",
    "cnpj": "11.444.777/0001-61",
    "nome": "Ana",
    "email": "ana@nova.com",
    "senha": "senha123",
}


def test_health_responde_ok(cliente):
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok", "banco": "conectado"}


def test_login_devolve_token_e_usuario_sem_senha(cliente, dados):
    resposta = cliente.post(
        "/auth/login", json={"email": "ADMIN@a.com ", "senha": "senha123"}
    )
    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["access_token"]
    assert corpo["usuario"]["email"] == "admin@a.com"
    assert not any("senha" in chave for chave in corpo["usuario"])


def test_login_com_senha_errada_responde_401_no_envelope(cliente, dados):
    resposta = cliente.post(
        "/auth/login", json={"email": "admin@a.com", "senha": "errada"}
    )
    assert resposta.status_code == 401
    assert erro(resposta) == {
        "codigo": "HTTP-401",
        "mensagem": "E-mail ou senha inválidos.",
        "campo": None,
    }


def test_rota_protegida_sem_token_responde_401(cliente):
    resposta = cliente.get("/auth/me")
    assert resposta.status_code == 401
    assert erro(resposta)["codigo"] == "HTTP-401"
    assert "Bearer" in erro(resposta)["mensagem"]


def test_me_devolve_o_dono_do_token(cliente, h_operador):
    resposta = cliente.get("/auth/me", headers=h_operador)
    assert resposta.status_code == 200
    assert resposta.get_json()["role"] == "OPERADOR"


def test_register_cria_empresa_com_admin(cliente):
    resposta = cliente.post("/auth/register", json=NOVA_EMPRESA)
    assert resposta.status_code == 201
    assert resposta.get_json()["usuario"]["role"] == "ADMIN"


def test_register_com_cnpj_repetido_responde_422(cliente, dados):
    corpo = {**NOVA_EMPRESA, "cnpj": "12.345.678/0001-95"}
    resposta = cliente.post("/auth/register", json=corpo)
    assert resposta.status_code == 422
    assert erro(resposta)["campo"] == "cnpj"


def test_operador_nao_lista_usuarios_rn09(cliente, h_operador):
    resposta = cliente.get("/usuarios", headers=h_operador)
    assert resposta.status_code == 403
    assert erro(resposta)["codigo"] == "RN-09"


def test_operador_nao_cria_usuario_rn09(cliente, h_operador):
    corpo = {"nome": "Novo", "email": "novo@a.com", "senha": "senha123", "role": "OPERADOR"}
    resposta = cliente.post("/usuarios", json=corpo, headers=h_operador)
    assert resposta.status_code == 403
    assert erro(resposta)["codigo"] == "RN-09"


def test_ultimo_admin_nao_pode_ser_rebaixado(cliente, dados, h_admin):
    resposta = cliente.put(
        f"/usuarios/{dados.admin.id}", json={"role": "OPERADOR"}, headers=h_admin
    )
    assert resposta.status_code == 422
    assert erro(resposta)["campo"] == "role"


def test_usuario_nao_exclui_a_si_mesmo(cliente, dados, h_admin):
    resposta = cliente.delete(f"/usuarios/{dados.admin.id}", headers=h_admin)
    assert resposta.status_code == 422
    assert erro(resposta)["campo"] == "id"


def test_usuario_de_outra_empresa_responde_404_rn08(cliente, dados, h_admin):
    resposta = cliente.get(f"/usuarios/{dados.admin_b.id}", headers=h_admin)
    assert resposta.status_code == 404
    assert erro(resposta)["codigo"] == "HTTP-404"


def test_usuario_desativado_perde_acesso_na_hora(cliente, dados, h_admin, h_operador):
    assert cliente.delete(f"/usuarios/{dados.operador.id}", headers=h_admin).status_code == 204
    assert cliente.get("/auth/me", headers=h_operador).status_code == 401
