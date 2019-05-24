from flask import url_for


def test_login_redirect(client):
    response = client.get(url_for('account.login'))
    assert response.status_code == 302
    assert response.headers['Location'].endswith(url_for('github.login'))
