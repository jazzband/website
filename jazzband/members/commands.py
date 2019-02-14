import click
import click_log
import logging
from flask.cli import with_appcontext

from . import tasks

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


@click.command('members')
@click_log.simple_verbosity_option(logger)
@with_appcontext
def sync_members():
    "Syncs members"
    tasks.sync_members()


@click.command('emails')
@click.option('--user_id', '-u', default=None)
@click_log.simple_verbosity_option(logger)
@with_appcontext
def sync_email_addresses(user_id):
    "Sync email addresses for user"
    tasks.sync_email_addresses(user_id)
