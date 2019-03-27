from datetime import datetime

from .db import postgres
from .utils import sub_dict


class Syncable:
    synced_at = postgres.Column(
        postgres.DateTime, default=datetime.utcnow, nullable=False
    )

    @classmethod
    def sync(cls, data, key="id"):
        fields = [column.name for column in cls.__table__.columns]
        results = []
        for item in data:
            defaults = sub_dict(item, fields)
            results.append(
                cls.update_or_create(
                    defaults=defaults, commit=False, **{key: item[key]}
                )
            )
        postgres.session.commit()
        return results


@postgres.event.listens_for(Syncable, "before_update", propagate=True)
def timestamp_before_update(mapper, connection, target):
    # When a model with a timestamp is updated; force update the updated
    # timestamp.
    target.synced_at = datetime.utcnow()


class Helpers:
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
