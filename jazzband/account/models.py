from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy_utils import generic_repr

from ..db import postgres as db
from ..members.models import User


@generic_repr("id", "user_id", "provider", "created_at")
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    __tablename__ = "oauth"
    __table_args__ = (db.Index("provider", "user_id"),)
