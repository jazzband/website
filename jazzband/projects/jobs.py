from datetime import timedelta
from packaging.version import parse as parse_version

from . import commands
from .models import ProjectUpload
from ..db import postgres
from ..jobs import rq


@rq.job
def send_new_upload_notifications():
    commands.send_new_upload_notifications()


send_new_upload_notifications.schedule(
    timedelta(minutes=1),
    timeout=45,
    job_id='send-upload-notifications',
)


@rq.job
def update_upload_ordering(project_id):
    uploads = ProjectUpload.query.filter_by(project_id=project_id).all()

    def version_sorter(upload):
        return parse_version(upload.version)

    with postgres.transaction():
        for index, upload in enumerate(sorted(uploads, key=version_sorter)):
            upload.ordering = index
        postgres.session.commit()
