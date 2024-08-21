import json
from contextlib import contextmanager

import flask
from redis import Redis, Sentinel

from flask_session.defaults import Defaults
from flask_session.redis import RedisSentinelSession


class TestRedisSentinelSession:
    """This requires package: redis"""

    @contextmanager
    def setup_sentinel(self):
        self.sentinel = Sentinel(
            [("127.0.0.1", 26379), ("127.0.0.1", 26380), ("127.0.0.1", 26381)],
        )
        self.master: Redis = self.sentinel.master_for(
            Defaults.SESSION_REDIS_SENTINEL_MASTER_SET

        )
        try:
            self.master.flushall()
            yield
        finally:
            self.master.flushall()
            self.master.close()

    def retrieve_stored_session(self, key):
        return self.master.get(key)


    def test_redis_ha_default(self, app_utils):
        with self.setup_sentinel():
            app = app_utils.create_app(
                {"SESSION_TYPE": "redissentinel", "SESSION_REDIS_SENTINEL": self.sentinel}
            )

            with app.test_request_context():
                assert isinstance(flask.session, RedisSentinelSession)
                app_utils.test_session(app)

                # Check if the session is stored in Redis
                cookie = app_utils.test_session_with_cookie(app)
                session_id = cookie.split(";")[0].split("=")[1]
                byte_string = self.retrieve_stored_session(f"session:{session_id}")
                stored_session = (
                    json.loads(byte_string.decode("utf-8")) if byte_string else {}
                )
                assert stored_session.get("value") == "44"
