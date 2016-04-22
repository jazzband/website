from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from .github import github
from .utils import sub_dict

db = SQLAlchemy()


class Syncable(object):
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


@db.event.listens_for(Syncable, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    # When a model with a timestamp is updated; force update the updated
    # timestamp.
    target.synced_at = datetime.utcnow()


class Helpers(object):

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

    @classmethod
    def update_or_create(cls, defaults=None, commit=True, **kwargs):
        if defaults is None:
            defaults = {}
        instance = cls.query.filter_by(**kwargs).first()
        if instance:
            for arg, value in defaults.iteritems():
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


managers = db.Table('managers',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id')),
)


class Project(db.Model, Helpers, Syncable):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    html_url = db.Column(db.String(255))
    subscribers_count = db.Column(db.SmallInteger, default=0, nullable=False)
    stargazers_count = db.Column(db.SmallInteger, default=0, nullable=False)
    forks_count = db.Column(db.SmallInteger, default=0, nullable=False)
    open_issues_count = db.Column(db.SmallInteger, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    managers = db.relationship('User', secondary=managers,
                               backref=db.backref('projects', lazy='dynamic'))

    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    pushed_at = db.Column(db.DateTime, nullable=True)

    __tablename__ = 'projects'
    __table_args__ = (
    )

    def __repr__(self):
        return '<Project %s: %s (%s)>' % (self.id, self.name, self.id)


class User(db.Model, Helpers, Syncable, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(39), unique=True, nullable=False, index=True)
    avatar_url = db.Column(db.String(255))
    html_url = db.Column(db.String(255))
    is_member = db.Column(db.Boolean, default=False, nullable=False,
                          index=True)
    is_roadie = db.Column(db.Boolean, default=False, nullable=False,
                          index=True)
    is_banned = db.Column(db.Boolean, default=False, nullable=False,
                          index=True)
    access_token = db.Column(db.String(200))
    email_addresses = db.relationship('EmailAddress', backref='user',
                                      lazy='dynamic')

    __tablename__ = 'users'
    __table_args__ = (
        db.Index('member_not_banned', 'is_member', 'is_banned'),
    )

    def __unicode__(self):
        return self.login

    def __repr__(self):
        return '<User %s (%s)>' % (self.login, self.id)

    @property
    def is_active(self):
        return not self.is_banned

    def check_verified_emails(self):
        # User can have multiple emails,
        # we just want to ensure he has at least one:
        # see https://github.com/jazzband/website/issues/8 for more.
        return (self.email_addresses.filter_by(verified=True)
                                    .first() is not None)


class EmailAddress(db.Model, Helpers, Syncable):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    verified = db.Column(db.Boolean, default=True, nullable=False, index=True)
    primary = db.Column(db.Boolean, default=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    __tablename__ = 'email_addresses'
    __table_args__ = (
        db.Index('verified', 'primary'),
    )

    def __unicode__(self):
        return self.email

    def __repr__(self):
        meta = []
        if self.verified:
            meta.append('Verified')
        if self.primary:
            meta.append('Primary')
        meta = '(%s)' % ', '.join(meta)
        return '<EmailAddress %s %s>' % (self.email, meta)


def update_user_email_addresses(user):
    # fetch all the email addresses for the user with the given access token
    email_addresses = []
    if user.access_token:
        for email_item in github.get_emails(access_token=user.access_token):
            email_item['user_id'] = user.id
            email_addresses.append(email_item)
        EmailAddress.sync(email_addresses, key='email')
