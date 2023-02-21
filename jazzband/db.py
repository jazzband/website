from collections import deque
from contextlib import contextmanager

from flask_redis import FlaskRedis
from flask_sqlalchemy import Model, SQLAlchemy
from walrus import Walrus

from .exceptions import Rollback


class JazzbandModel(Model):
    @classmethod
    def update_or_create(cls, defaults=None, commit=True, **kwargs):
        if defaults is None:
            defaults = {}
        instance = cls.query.filter_by(**kwargs).first()
        if instance:
            for arg, value in defaults.items():
                setattr(instance, arg, value)
            if commit:
                postgres.session.commit()
            return instance, False
        else:
            params = kwargs.copy()
            params.update(defaults)
            instance = cls(**params)
            postgres.session.add(instance)
            if commit:
                postgres.session.commit()
            return instance, True

    def save(self, commit=True):
        postgres.session.add(self)
        if commit:
            postgres.session.commit()
        return self

    def delete(self, commit=True):
        postgres.session.delete(self)
        if commit:
            postgres.session.commit()
        return self


class JazzbandSQLAlchemy(SQLAlchemy):
    def init_app(self, app):
        super().init_app(app)
        app.config.setdefault("SQLALCHEMY_NESTED_TRANSACTION", False)
        app.config.setdefault("SQLALCHEMY_ISOLATE_TRANSACTION", True)
        # dispose of engine to fix issue with forks
        # https://virtualandy.wordpress.com/2019/09/04/a-fix-for-operationalerror-psycopg2-operationalerror-ssl-error-decryption-failed-or-bad-record-mac/
        with app.app_context():
            self.engine.dispose()


postgres = JazzbandSQLAlchemy(model_class=JazzbandModel)

redis = FlaskRedis.from_custom_provider(Walrus)
