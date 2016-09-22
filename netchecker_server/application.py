import datetime

from flask import abort
from flask import jsonify
from flask import Flask
from flask import request
import requests
import six

from netchecker_server import exceptions


app = Flask(__name__)
RECORDS = {}


K8S_API_URL = 'http://localhost:8001/api/v1/'


@app.errorhandler(exceptions.ConnectivityCheckError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def get_records(record_id):
    if record_id is None:
        return RECORDS
    elif record_id in RECORDS:
        return RECORDS[record_id]
    else:
        return None


def make_record(record_id, record_data):
    RECORDS[record_id] = record_data
    RECORDS[record_id]['last_updated'] = \
        datetime.datetime.now()


def outdated_resp(agent_id):
    return(
        datetime.datetime.now() - RECORDS[agent_id]['last_updated']
        > datetime.timedelta(minutes=2)
    )


@app.route('/api/v1/agents/')
@app.route('/api/v1/agents/<agent_uid>', methods=["GET", "POST"])
def process_agents_requests(agent_uid=None):
    if request.method == 'GET':
        records = get_records(agent_uid)
        if records is None:
            abort(404)
        return jsonify(**records)

    elif request.method == 'POST':
        if request.headers['Content-Type'] == 'application/json':
            make_record(agent_uid, request.json)
            return ("Record was set", 200)
        else:
            abort(403)


@app.route('/api/v1/connectivity_check')
def check_connectivity():
    query_params = {
        'labelSelector': 'app in (netchecker-agent, netchecker-agent-hostnet)'
    }
    pods_from_api = requests.get(K8S_API_URL + 'pods', query_params)
    pod_names = set([
        pod['metadata']['name'] for pod in pods_from_api.json()['items']
    ])

    absent_pods = pod_names - set(six.iterkeys(RECORDS))
    outdated_pods = set([
        pod for pod in pod_names - absent_pods if outdated_resp(pod)])

    if absent_pods or outdated_pods:
        raise exceptions.ConnectivityCheckError(
            'Connectivity check fails for pods [{}]'
            .format(', '.join(absent_pods | outdated_pods)),
            payload={'absent': list(absent_pods),
                     'outdated': list(outdated_pods)}
        )

    return jsonify(
        reported_agents_count=len(RECORDS),
        message=(
            'All {} pods successfully reported back to the server'
            .format(len(RECORDS))
        )
    )
