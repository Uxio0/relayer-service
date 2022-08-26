import os
from typing import Any, Dict

from flask import Flask, redirect, url_for

from eth_typing import HexStr

from .services import relay_transaction
from .version import VERSION


def create_app(test_config=None) -> Flask:
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.errorhandler(ValueError)
    def handle_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        return {
            "code": 422,
            "name": "ServiceError",
            "description": e.args[0] if e.args else "",
        }

    @app.route("/")
    def home():
        return redirect(url_for("about"))

    @app.route("/about/")
    def about() -> Dict[str, Any]:
        return {"version": VERSION}

    @app.route("/health/")
    def health() -> str:
        return "OK"

    @app.route(
        "/v1/<int:chain_id>/relayed-transactions/<safe_tx_hash>/", methods=["POST"]
    )
    def relay(chain_id: int, safe_tx_hash: HexStr) -> Dict[str, Any]:
        return {"tx_hash": relay_transaction(chain_id, safe_tx_hash).hex()}

    return app
