import logging
from datetime import datetime

from flask import render_template
from flask_mail import Message
from packaging.version import parse as parse_version
from spinach import Tasks

from ..db import postgres
from ..email import mail
from ..members.models import User, EmailAddress
from .models import ProjectMembership, ProjectUpload

logger = logging.getLogger(__name__)

tasks = Tasks()


@tasks.task(name="send_new_upload_notifications")
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


# send_new_upload_notifications.schedule(
#     timedelta(minutes=1),
#     timeout=45,
#     job_id='send-upload-notifications',
# )


@tasks.task(name='update_upload_ordering')
def update_upload_ordering(project_id):
    uploads = ProjectUpload.query.filter_by(project_id=project_id).all()

    def version_sorter(upload):
        return parse_version(upload.version)

    with postgres.transaction():
        for index, upload in enumerate(sorted(uploads, key=version_sorter)):
            upload.ordering = index
        postgres.session.commit()
