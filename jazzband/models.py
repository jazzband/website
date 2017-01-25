from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from .utils import sub_dict

db = SQLAlchemy()


class Syncable(object):
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def sync(cls, data, key='id'):
        fields = [column.name for column in cls.__table__.columns]
        results = []
        for item in data:
            defaults = sub_dict(item, fields)
            results.append(
                cls.update_or_create(
                    defaults=defaults,
                    commit=False,
                    **{key: item[key]}
                )
            )
        db.session.commit()
        return results


@db.event.listens_for(Syncable, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    # When a model with a timestamp is updated; force update the updated
    # timestamp.
    target.synced_at = datetime.utcnow()


class Helpers(object):

    @classmethod
    def update_or_create(cls, defaults=None, commit=True, **kwargs):
        if defaults is None:
            defaults = {}
        instance = cls.query.filter_by(**kwargs).first()
        if instance:
            for arg, value in defaults.items():
                setattr(instance, arg, value)
            if commit:
                db.session.commit()
            return instance, False
        else:
            params = kwargs.copy()
            params.update(defaults)
            instance = cls(**params)
            db.session.add(instance)
            if commit:
                db.session.commit()
            return instance, True

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()
        return self
