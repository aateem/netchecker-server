from flask import url_for, json
import pytest

from netchecker_server import application


@pytest.fixture
def client():
    return application.app.test_client()


@pytest.fixture
def prefiled_records(request):
    expected_data = {
        'agent_one': {'key': 'value'},
        'agent_two': {'different_key': 'different_value'},
    }
    application.RECORDS.update(expected_data)

    def fin():
        application.RECORDS = {}

    request.addfinalizer(fin)

    return expected_data


@pytest.fixture
def agents_url():
    with application.app.test_request_context():
        url = url_for('process_agents_requests')

    return url


@pytest.fixture
def agent_one_url():
    with application.app.test_request_context():
        url = url_for('process_agents_requests', agent_uid='agent_one')

    return url


def test_get_agents_from_empty_records(client, agents_url):
    resp = client.get(agents_url)
    data = json.loads(resp.get_data())
    assert data == {}


def test_get_on_agents_returns_all_records(client, agents_url,
                                           prefiled_records):
    resp = client.get(agents_url)
    data = json.loads(resp.get_data())
    assert data == prefiled_records


def test_get_returns_404_on_non_existing_obj(client, agent_one_url):
    resp = client.get(agent_one_url)
    assert resp.status_code == 404


def test_get_returns_proper_value(client, agent_one_url, prefiled_records):
    resp = client.get(agent_one_url)
    data = json.loads(resp.get_data())

    assert len(data) == 1
    assert data == prefiled_records['agent_one']


def test_put_is_not_allowed(client, agents_url):
    resp = client.put(agents_url)
    assert resp.status_code == 405


def test_post_with_diff_content_type_forbidden(client, agent_one_url):
    resp = client.post(agent_one_url, content_type='text/html')
    assert resp.status_code == 403


def test_post_is_not_allowed_for_agents(client, agents_url):
    resp = client.post(agents_url)
    assert resp.status_code == 405


def test_set_record(client, agent_one_url):
    expected = {'key_one': 'value_one'}
    resp = client.post(agent_one_url, data=json.dumps(expected),
                       content_type='application/json')

    assert resp.status_code == 200
    assert application.RECORDS.get('agent_one') is not None


def test_post_overrides_data(client, agent_one_url, prefiled_records):
    expected = {'key_three': 'value_three'}
    resp = client.post(agent_one_url, data=json.dumps(expected),
                       content_type='application/json')

    assert resp.status_code == 200

    for key in expected:
        assert expected[key] == application.RECORDS['agent_one'][key]
