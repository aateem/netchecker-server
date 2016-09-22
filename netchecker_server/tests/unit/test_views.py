import datetime

from flask import url_for, json
import pytest
import requests_mock

from netchecker_server import application


@pytest.fixture
def client():
    return application.app.test_client()


@pytest.fixture
def prefilled_records(request):
    now = datetime.datetime.now()
    expected_data = {
        'agent_one': {'key': 'value', 'last_updated': now},
        'agent_two': {'key': 'different_value', 'last_updated': now},
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


@pytest.fixture
def connectivity_check_url():
    with application.app.test_request_context():
        url = url_for('check_connectivity')

    return url


def test_get_agents_from_empty_records(client, agents_url):
    resp = client.get(agents_url)
    data = json.loads(resp.get_data())
    assert data == {}


def test_get_on_agents_returns_all_records(client, agents_url,
                                           prefilled_records):
    resp = client.get(agents_url)
    data = json.loads(resp.get_data())
    exact_keys = ('key',)
    for agent in data:
        for key in exact_keys:
            assert data[agent][key] == prefilled_records[agent][key]

        assert data[agent]['last_updated']


def test_get_returns_404_on_non_existing_obj(client, agent_one_url):
    resp = client.get(agent_one_url)
    assert resp.status_code == 404


def test_get_returns_proper_value(client, agent_one_url, prefilled_records):
    resp = client.get(agent_one_url)
    data = json.loads(resp.get_data())
    exact_keys = ('key',)
    for key in exact_keys:
        assert data[key] == prefilled_records['agent_one'][key]


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
    assert resp.data.decode('utf-8') == u"Record was set"
    assert application.RECORDS.get('agent_one') is not None


def test_post_overrides_data(client, agent_one_url, prefilled_records):
    expected = {'key_three': 'value_three'}
    resp = client.post(agent_one_url, data=json.dumps(expected),
                       content_type='application/json')

    assert resp.status_code == 200

    for key in expected:
        assert expected[key] == application.RECORDS['agent_one'][key]


@pytest.fixture
def k8s_pods():
    return {
        'items': [
            {'metadata': {'name': 'agent_one'}},
            {'metadata': {'name': 'agent_two'}}
        ]
    }


def get_connectivity_resp(client, url, mock_resp_json):
    with requests_mock.Mocker() as m:
        m.register_uri('GET', application.K8S_API_URL + 'pods',
                       json=mock_resp_json)

        resp = client.get(url)

    return resp


def check_error_resp(resp):
    assert resp.status_code == 400
    assert resp.data.decode('utf-8') == \
        (u"Pods without responses - [agent_two]. "
         u"Pods with outdated responses - [].")


def test_check_connectivity_success(client, connectivity_check_url,
                                    prefilled_records, k8s_pods):

    resp = get_connectivity_resp(client, connectivity_check_url, k8s_pods)
    assert resp.status_code == 200
    data = json.loads(resp.get_data())
    assert data['message'] == (
        u'All {} pods successfully reported back to the server'
        .format(len(application.RECORDS))
    )
    assert data['reported_agents_count'] == len(application.RECORDS)


def test_check_cnnty_agent_not_present_in_records(client, prefilled_records,
                                                  connectivity_check_url,
                                                  k8s_pods):
    del application.RECORDS['agent_two']
    resp = get_connectivity_resp(client, connectivity_check_url, k8s_pods)

    assert resp.status_code == 400

    data = json.loads(resp.get_data())
    assert data['message'] == \
        u'Connectivity check fails for pods [agent_two]'
    assert data['absent'] == ['agent_two']
    assert data['outdated'] == []


def make_outdated(agent):
    outdated = (
        application.RECORDS[agent]['last_updated'] -
        datetime.timedelta(minutes=3)
    )
    application.RECORDS[agent]['last_updated'] = outdated


def test_check_cnnty_agent_response_is_outdated(client, prefilled_records,
                                                connectivity_check_url,
                                                k8s_pods):
    make_outdated('agent_two')
    resp = get_connectivity_resp(client, connectivity_check_url, k8s_pods)

    assert resp.status_code == 400

    data = json.loads(resp.get_data())
    assert data['message'] == \
        u'Connectivity check fails for pods [agent_two]'
    assert data['absent'] == []
    assert data['outdated'] == ['agent_two']


def test_check_cnnty_and_outdated_in_response(client, prefilled_records,
                                              connectivity_check_url,
                                              k8s_pods):
    del application.RECORDS['agent_two']
    make_outdated('agent_one')
    resp = get_connectivity_resp(client, connectivity_check_url, k8s_pods)

    assert resp.status_code == 400
    data = json.loads(resp.get_data())
    assert u'Connectivity check fails for pods' in data['message']
    assert u'agent_one' in data['message']
    assert u'agent_two' in data['message']
    assert data['absent'] == ['agent_two']
    assert data['outdated'] == ['agent_one']
