import argparse
import logging

from requestlogger import WSGILogger, ApacheFormatter
from waitress import serve

from netchecker_server.application import app


def run():
    parser = argparse.ArgumentParser(description='HTTP Server')
    parser.add_argument('ip', help='HTTP Server IP')
    parser.add_argument('port', type=int,
                        help='Listening port for HTTP Server')
    args = parser.parse_args()

    # setup reqests' logging
    handlers = [logging.StreamHandler()]
    # propagate == False - do not propagate debug log messages
    # from requestlogger to root logger's stream handler
    logging_app = WSGILogger(app, handlers, ApacheFormatter(), propagate=False)
    serve(logging_app, host=args.ip, port=args.port)


if __name__ == '__main__':
    run()
