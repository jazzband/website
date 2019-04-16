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
