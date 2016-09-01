import datetime

from flask import abort
from flask import jsonify
from flask import Flask
from flask import request
import requests


app = Flask(__name__)
RECORDS = {}


K8S_API_URL = 'http://localhost:8001/api/v1/'


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
    pod_names = [
        pod['metadata']['name'] for pod in pods_from_api.json()['items']
    ]

    absent_pods = []
    for pod in pod_names:
        if not (pod in RECORDS) or outdated_resp(pod):
            absent_pods.append(pod)

    if absent_pods:
        return (
            'There is no network connectivity with pods {}'
            .format(', '.join(absent_pods)),
            400
        )

    return ('', 204)
