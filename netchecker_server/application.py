import time

from flask import abort
from flask import jsonify
from flask import Flask
from flask import request


app = Flask(__name__)
RECORDS = {}


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
        time.strftime('%Y-%m-%d %H:%M:%S')


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
            return "Record was set"
        else:
            abort(403)
