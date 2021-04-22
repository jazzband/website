from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.sql import expression
from sqlalchemy_utils import generic_repr

from ..db import postgres as db
from ..mixins import Syncable


@generic_repr("login", "id")
class User(db.Model, Syncable, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(39), unique=True, nullable=False, index=True)
    avatar_url = db.Column(db.String(255))
    html_url = db.Column(db.String(255))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime, nullable=True)
    is_member = db.Column(
        db.Boolean,
        server_default=expression.false(),
        default=False,
        nullable=False,
        index=True,
    )
    is_roadie = db.Column(
        db.Boolean,
        server_default=expression.false(),
        default=False,
        nullable=False,
        index=True,
    )
    is_banned = db.Column(
        db.Boolean,
        server_default=expression.false(),
        default=False,
        nullable=False,
        index=True,
    )
    is_restricted = db.Column(
        db.Boolean,
        server_default=expression.false(),
        default=False,
        nullable=False,
        index=True,
    )
    consented_at = db.Column(db.DateTime, nullable=True)
    profile_consent = db.Column(
        db.Boolean, server_default=expression.false(), default=False, nullable=False
    )
    org_consent = db.Column(
        db.Boolean, server_default=expression.false(), default=False, nullable=False
    )
    cookies_consent = db.Column(
        db.Boolean, server_default=expression.false(), default=False, nullable=False
    )
    age_consent = db.Column(
        db.Boolean, server_default=expression.false(), default=False, nullable=False
    )
    has_2fa = db.Column(
        db.Boolean,
        default=False,
        server_default=expression.false(),
        nullable=False,
        index=True,
    )
    email_addresses = db.relationship("EmailAddress", backref="user", lazy="dynamic")
    projects_memberships = db.relationship(
        "ProjectMembership", backref="user", lazy="dynamic"
    )
    oauths = db.relationship("OAuth", backref="user", lazy="dynamic")

    __tablename__ = "users"
    __table_args__ = (db.Index("member_not_banned", "is_member", "is_banned"),)

    def __str__(self):
        return self.login

    @classmethod
    def roadies(cls):
        return cls.query.filter(cls.is_roadie.is_(True))

    @classmethod
    def active_members(cls):
        return cls.query.filter(
            cls.is_member.is_(True),
            cls.is_banned.is_(False),
            cls.is_restricted.is_(False),
            cls.login != "jazzband-bot",
        )

    @property
    def access_token(self):
        oauth = self.oauths.scalar()
        if oauth is None:
            return
        return oauth.token.get("access_token", None)

    @property
    def has_consented(self):
        return (
            self.profile_consent
            and self.org_consent
            and self.cookies_consent
            and self.age_consent
        )

    @property
    def is_active(self):
        return not self.is_banned

    @property
    def has_verified_emails(self):
        # User can have multiple emails,
        # we just want to ensure he has at least one:
        # see https://github.com/jazzband/website/issues/8 for more.
        return (
            EmailAddress.query.filter_by(user_id=self.id, verified=True).first()
            is not None
        )


@generic_repr("email", "user_id", "verified", "primary")
class EmailAddress(db.Model, Syncable):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    verified = db.Column(db.Boolean, default=True, nullable=False, index=True)
    primary = db.Column(db.Boolean, default=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    __tablename__ = "email_addresses"
    __table_args__ = (db.Index("verified", "primary"),)

    def __str__(self):
        return self.email
