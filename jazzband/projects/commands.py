from datetime import datetime

import click
import click_log
import logging
from flask import render_template
from flask.cli import with_appcontext
from flask_mail import Message

from ..db import postgres
from ..email import mail
from ..github import github
from ..members.models import User, EmailAddress
from .models import Project, ProjectMembership, ProjectUpload

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


@click.command('projects')
@with_appcontext
def sync_projects():
    "Syncs projects"
    projects_data = github.get_projects()
    Project.sync(projects_data)


@click.command('new_upload_notifications')
@click_log.simple_verbosity_option(logger)
@with_appcontext
def send_new_upload_notifications(project_id=None):
    "Sends project upload notifications if needed"
    unnotified_uploads = ProjectUpload.query.filter_by(notified_at=None)
    if project_id is not None:
        unnotified_uploads = unnotified_uploads.filter_by(
            project_id=project_id,
        )
    messages = []

    for upload in unnotified_uploads:
        lead_memberships = upload.project.membership.join(
            ProjectMembership.user
        ).filter(
            ProjectMembership.is_lead == True,
            User.is_member == True,
            User.is_banned == False,
        )
        lead_members = [membership.user for membership in lead_memberships]

        recipients = []

        for lead_member in lead_members + list(User.roadies()):

            primary_email = lead_member.email_addresses.filter(
                EmailAddress.primary == True,
                EmailAddress.verified == True,
            ).first()

            if not primary_email:
                continue

            recipients.append(primary_email.email)

        message = Message(
            subject=f'Project {upload.project.name} received a new upload',
            recipients=recipients,
            body=render_template(
                'projects/mails/new_upload_notification.txt',
                project=upload.project,
                upload=upload,
                lead_members=lead_members,
            )
        )
        messages.append((upload, message))

    if not messages:
        logger.info('No uploads found without notifications.')
        return

    with mail.connect() as smtp:
        for upload, message in messages:
            with postgres.transaction():
                try:
                    smtp.send(message)
                finally:
                    upload.notified_at = datetime.utcnow()
                    upload.save()
                    logger.info(f'Send notification for upload {upload}.')
