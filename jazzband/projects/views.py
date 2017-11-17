import hashlib
import hmac
import os
import shutil
import tempfile
from datetime import datetime
from pkg_resources import safe_name

import delegator
import requests
from flask import (Blueprint, current_app, flash, jsonify, make_response,
                   redirect, render_template, request, safe_join,
                   send_from_directory, url_for)
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_mail import Message
from requests.exceptions import HTTPError
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func
from werkzeug import secure_filename

from ..decorators import http_cache, templated
from ..members.models import User, EmailAddress
from ..email import mail
from ..errors import sentry
from ..exceptions import eject
from .forms import DeleteForm, ReleaseForm, UploadForm
from .models import db, Project, ProjectMembership, ProjectUpload


projects = Blueprint('projects', __name__, url_prefix='/projects')

MAX_FILESIZE = 60 * 1024 * 1024  # 60M
MAX_SIGSIZE = 8 * 1024           # 8K
SIGNATURE_START = b'-----BEGIN PGP SIGNATURE-----'
PATH_HASHER = 'sha256'
DEFAULT_SORTER = func.random()
SORTER = {
    'uploads': Project.uploads_count,
    'watchers': Project.subscribers_count,
    'stargazers': Project.stargazers_count,
    'forks': Project.forks_count,
    'issues': Project.open_issues_count,
    'name': Project.name,
    'random': DEFAULT_SORTER,
}
DEFAULT_ORDER = 'desc'


@projects.route('')
@http_cache()
@templated()
def index():
    sorter = request.args.get('sorter', None)
    if sorter is None:
        sorter = 'random'
        initial_sorting = True
    else:
        initial_sorting = False
    order = request.args.get('order', None)
    criterion = SORTER.get(sorter, DEFAULT_SORTER)
    if order == DEFAULT_ORDER:
        criterion = desc(criterion)

    projects = Project.query.filter_by(
        is_active=True,
    ).filter(
        Project.name != 'website',
        Project.name != 'roadies'
    ).order_by(
        criterion
    )
    return {
        'projects': projects,
        'sorter': sorter,
        'initial_sorting': initial_sorting,
        'order': order,
        'DEFAULT_ORDER': DEFAULT_ORDER,
    }


class DetailView(MethodView):
    """
    A view to show the details of a project.
    """
    methods = ['GET']
    decorators = [templated()]

    def get_project(self, name):
        return Project.query.filter_by(name=name).first_or_404()

    def dispatch_request(self, *args, **kwargs):
        self.project = self.get_project(kwargs.get('name'))
        return super().dispatch_request(*args, **kwargs)

    def get(self, name):
        return {
            'project': self.project,
            'uploads': self.project.uploads.order_by(
                ProjectUpload.version.desc()
            ),
        }


class UploadsBaseView(MethodView):
    anon_methods = None

    def get_upload(self, upload_id):
        return ProjectUpload.query.filter_by(id=upload_id).first_or_404()

    def get_project(self, name):
        projects = Project.query.filter(Project.name == name)
        if self.anon_methods and request.method not in self.anon_methods:
            projects = projects.filter(
                Project.membership.any(is_lead=True),
                Project.membership.any(user=current_user),
            )
        return projects.first_or_404()

    def dispatch_request(self, *args, **kwargs):
        self.project = self.get_project(kwargs.get('name'))
        upload_id = kwargs.get('upload_id')
        if upload_id:
            self.upload = self.get_upload(upload_id)
        else:
            self.upload = None
        return super().dispatch_request(*args, **kwargs)

    def redirect_to_uploads(self):
        return redirect(
            url_for('projects.uploads', name=self.project.name)
        )


class UploadsView(UploadsBaseView):
    """
    A view to show the details of a project and also handling file uploads
    via Twine/distutils.
    """
    methods = ['GET', 'POST']
    anon_methods = ['POST']
    decorators = [
        templated('projects/uploads/index.html'),
    ]

    def check_authentication(self):
        """
        Authenticate a request using a Redis lookup.
        """
        if request.authorization is None:
            return False
        return self.project.credentials.filter_by(
            is_active=True,
            username=request.authorization.username,
            password=request.authorization.password,
        ).scalar()

    def send_notifications(self, upload):
        lead_memberships = self.project.membership.join(
            ProjectMembership.user
        ).filter(
            ProjectMembership.is_lead == True,
            User.is_member == True,
            User.has_2fa == True,
            User.is_banned == False,
        )
        lead_members = [membership.user for membership in lead_memberships]

        recipients = []

        for lead_member in lead_members:

            primary_email = lead_member.email_addresses.filter(
                EmailAddress.primary == True,
                EmailAddress.verified == True,
            ).first()

            if not primary_email:
                continue

            recipients.append(primary_email.email)

        message = Message(
            subject=(
                f'[Jazzband] Project {self.project.name} received a new upload'
            ),
            recipients=recipients,
            bcc=list(User.roadies()),
            body=render_template(
                'projects/mails/project_upload_notification.txt',
                project=self.project,
                upload=upload,
            )
        )
        mail.send(message)

    def get(self, name):
        return {
            'project': self.project,
            'uploads': self.project.uploads.order_by(
                ProjectUpload.version.desc()
            ),
        }

    def post(self, name):
        if not self.check_authentication():
            response = make_response('', 401)
            response.headers["WWW-Authenticate"] = 'Basic realm="Jazzband"'
            return response

        # distutils "helpfully" substitutes unknown, but "required" values
        # with the string "UNKNOWN". This is basically never what anyone
        # actually wants so we'll just go ahead and delete anything whose
        # value is UNKNOWN.
        form_copy = request.form.copy()
        unknown_found = False
        for key, value in request.form.items():
            if value == 'UNKNOWN':
                unknown_found = True
                form_copy.pop(key)
        if unknown_found:
            request.form = form_copy

        form = UploadForm(meta={'csrf': False})

        validation_order = [
            'name',
            'version',
            'content',
        ]
        if not form.validate_on_submit():
            for field_name in validation_order:
                if field_name in form.errors:
                    break
            else:
                field_name = sorted(form.errors.keys())[0]

            print(form.errors)
            eject(
                400,
                description='%s: %s' %
                            (field_name, ', '.join(form.errors[field_name]))
            )

        # the upload FileStorage
        upload_data = form.content.data

        if upload_data is None:
            eject(400, description='Upload payload does not have a file.')

        upload_filename = secure_filename(upload_data.filename)

        # Make sure that our filename matches the project that it is being
        # uploaded to.
        prefix = safe_name(self.project.name).lower()
        if not safe_name(upload_filename).lower().startswith(prefix):
            eject(
                400,
                description='The filename for %r must start with %r.' %
                            (self.project.name, prefix)
            )

        # Fail if a project upload already exists
        if ProjectUpload.query.filter_by(
                filename=upload_filename, project_id=self.project.id).scalar():
            eject(400, description='File already exists.')

        # Store file uploads and calculate hashes
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_path = os.path.join(tmpdir, upload_filename)
            upload_data.stream.seek(0)
            upload_data.save(upload_path)

            # Buffer the entire file onto disk, checking the hash of the file
            # as we go along.
            with open(upload_path, 'rb') as upload_file:
                file_hashes = {
                    'md5': hashlib.md5(),
                    'sha256': hashlib.sha256(),
                    'blake2_256': hashlib.blake2b(digest_size=256 // 8),
                }
                for chunk in iter(lambda: upload_file.read(8096), b''):
                    for hasher in file_hashes.values():
                        hasher.update(chunk)

            # Take our hash functions and compute the final hashes for them
            # now.
            file_hashes = {
                method: file_hash.hexdigest().lower()
                for method, file_hash in file_hashes.items()
            }

            # Actually verify the digests that we've gotten. We're going to use
            # hmac.compare_digest even though we probably don't actually need
            # to because it's better safe than sorry. In the case of multiple
            # digests we expect them all to be given.
            hash_comparisons = [
                hmac.compare_digest(
                    getattr(form, '%s_digest' % digest_name).data.lower(),
                    digest_value,
                )
                for digest_name, digest_value in file_hashes.items()
                if getattr(form, '%s_digest' % digest_name).data
            ]
            if not all(hash_comparisons):
                eject(
                    400,
                    description='The digest supplied does not match a digest '
                                'calculated from the uploaded file.',
                )

            # Also buffer the entire signature file to disk.
            signature = form.gpg_signature.data
            signature_filename = upload_filename + '.asc'
            if signature:
                signature_path = os.path.join(tmpdir, signature_filename)
                signature.stream.seek(0)
                signature.save(signature_path)
                if os.path.getsize(signature_path) > MAX_SIGSIZE:
                    eject(400, description='Signature too large.')

                # Check whether signature is ASCII armored
                with open(signature_path, 'rb') as signature_file:
                    if not signature_file.read().startswith(SIGNATURE_START):
                        eject(
                            400,
                            description='PGP signature is not ASCII armored.',
                        )

            version = form.version.data
            upload = ProjectUpload(
                version=version,
                project=self.project,
                # e.g. acme/2coffee12345678123123123123123123
                path=safe_join(self.project.name, file_hashes[PATH_HASHER]),
                filename=upload_filename,
                size=os.path.getsize(upload_path),
                md5_digest=file_hashes['md5'],
                sha256_digest=file_hashes['sha256'],
                blake2_256_digest=file_hashes['blake2_256'],
                form_data=request.form,
            )

            # make the storage path directory /app/uploads/acme
            os.makedirs(os.path.dirname(upload.full_path), exist_ok=True)
            # move the uploaded file to storage path directory
            shutil.move(upload_path, upload.full_path)
            # copy the uploaded signature file to storage path directory
            if signature:
                shutil.move(signature_path, upload.full_path + '.asc')
            # write to database
            upload.save()

        # self.send_notifications(upload)
        return 'OK'


class UploadsDownloadView(UploadsBaseView):
    methods = ['GET']
    decorators = [login_required]

    def get(self, name, upload_id):
        cache_timeout = current_app.get_send_file_max_age(
            self.upload.full_path
        )
        path, filename = os.path.split(self.upload.full_path)
        return send_from_directory(
            path,
            filename,
            cache_timeout=cache_timeout,
            as_attachment=True,
            attachment_filename=self.upload.filename,
            add_etags=False,
            conditional=True,
        )


class UploadsFormDataView(UploadsBaseView):
    methods = ['GET']
    decorators = [login_required]

    def get(self, name, upload_id):
        return jsonify(self.upload.form_data)


class UploadsReleaseView(UploadsBaseView):
    methods = ['GET', 'POST']
    decorators = [
        login_required,
        templated('projects/uploads/release.html'),
    ]

    def validate_upload(self):
        errors = []
        try:
            # check pypi if file was added, check sha256 digest, size and
            # filename
            pypi_response = requests.get(self.upload.project.pypi_json_url)
            pypi_response.raise_for_status()
            data = pypi_response.json()
        except HTTPError as exc:
            # in case there was a network issue with getting the JSON
            # data from PyPI
            sentry.captureException()
            errors.append(f'Error while validating upload: {exc}')
        except ValueError as exc:
            # or something was wrong about the returned JSON data
            sentry.captureException()
            errors.append(
                f'Error while parsing response from PyPI during validation: {exc}'
            )
        except Exception as exc:
            sentry.captureException()
            errors.append(f'Unknown error: {exc}')
        else:
            # next check the data for what we're looking for
            releases = data.get('releases', {})
            release_files = releases.get(self.upload.version, [])

            if release_files:
                for release_file in release_files:
                    release_fiename = release_file.get('filename', None)
                    if release_filename is None:
                        errors.append('No file found.')
                        sentry.captureMessage(
                            'No file found in validation response.'
                        )

                    if release_fiename == self.upload.filename:
                        digests = release_file.get('digests', {})
                        if digests:
                            md5_digest = digests.get('md5', None)
                            if (md5_digest and
                                    md5_digest != self.upload.md5_digest):
                                error = (
                                    f'MD5 hash of {self.upload.filename} does '
                                    f'not match hash returned by PyPI.'
                                )
                                errors.append(error)
                                sentry.captureMessage(error)

                            sha256_digest = digests.get('sha256', None)
                            if (sha256_digest and
                                    sha256_digest !=
                                    self.upload.sha256_digest):
                                error = (
                                    f'SHA256 hash of {self.upload.filename} '
                                    f'does not match hash returned by PyPI.'
                                )
                                errors.append(error)
                                sentry.captureMessage(error)
                        else:
                            error = (
                                f'No digests for file {self.upload.filename}'
                            )
                            errors.append(error)
                            sentry.captureMessage(error)
            else:
                error = (
                    f'No released files found for upload '
                    f'{self.upload.filename}'
                )
                errors.append(error)
                sentry.captureMessage(error)
        return errors

    def post(self, name, upload_id):
        if not current_user.has_2fa:
            message = (
                f"To release {self.upload.filename} you need to have "
                f"Two Factor Auth (2FA) enabled on GitHub."
            )
            flash(message)
            sentry.captureMessage(message)
            return self.redirect_to_uploads()

        if self.upload.released_at:
            flash(
                f"The upload {self.upload.filename} has already been released "
                f"and can't be released again."
            )
            return self.redirect_to_uploads()

        release_form = ReleaseForm(project_name=self.project.name)

        context = {
            'release_form': release_form,
            'project': self.project,
            'upload': self.upload,
        }

        if release_form.validate_on_submit():
            # copy path to new tmp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                upload_path = os.path.join(tmpdir, self.upload.filename)
                shutil.copy(self.upload.full_path, upload_path)

                # run twine upload against copied upload file
                twine_run = delegator.run(f'twine upload {upload_path}')

            if twine_run.return_code == 0:
                errors = self.validate_upload()
                release_form.add_global_error(*errors)
                if not errors:
                    # create ProjectRelease object with reference to project
                    self.upload.released_at = datetime.utcnow()
                    # write to database
                    self.upload.save()
                    message = (
                        f"You've successfully released {self.upload} to PyPI."
                    )
                    flash(message)
                    sentry.captureMessage(message)
                    return self.redirect_to_uploads()
            else:
                error = (
                    f'Upload failed. See standard output and error '
                    f'values below.'
                )
                release_form.add_global_error(error)
                sentry.captureMessage(error)
                sentry.captureMessage('Out:' + twine_run.out)
                sentry.captureMessage('Err:' + twine_run.err)
            context.update({
                'twine_run': twine_run,
                'upload': self.upload,
            })

        return context

    def get(self, name, upload_id):
        if self.upload.released_at:
            message = (
                f"The upload {self.upload.filename} has already been released "
                f"and can't be released again."
            )
            flash(message)
            sentry.captureMessage(message)
            return self.redirect_to_uploads()

        release_form = ReleaseForm(project_name=self.project.name)
        return {
            'project': self.project,
            'release_form': release_form,
            'upload': self.upload,
        }


class UploadsDeleteView(UploadsBaseView):
    methods = ['GET', 'POST']
    decorators = [
        login_required,
        templated('projects/uploads/delete.html'),
    ]

    def get(self, name, upload_id):
        if self.upload.released_at:
            message = (
                f"The upload {self.upload.filename} has already been "
                f"released and can't be deleted."
            )
            flash(message)
            sentry.captureMessage(message)
            return self.redirect_to_uploads()

        return {
            'project': self.project,
            'upload': self.upload,
            'delete_form': DeleteForm(project_name=self.project.name),
        }

    def post(self, name, upload_id):
        if not current_user.has_2fa:
            message = (
                f"To delete {self.upload.filename} you need to have "
                f"Two Factor Auth (2FA) enabled on GitHub."
            )
            flash(message)
            sentry.captureMessage(message)
            return self.redirect_to_uploads()

        if self.upload.released_at:
            message = (
                f"The upload {self.upload.filename} has already been "
                f"released and can't be deleted."
            )
            flash(message)
            sentry.captureMessage(message)
            return self.redirect_to_uploads()

        delete_form = DeleteForm(project_name=self.project.name)
        context = {
            'delete_form': delete_form,
            'project': self.project,
            'upload': self.upload,
        }

        if delete_form.validate_on_submit():
            self.upload.delete()
            message = (
                f"You've successfully deleted the upload "
                f"{self.upload.filename}."
            )
            flash(message)
            sentry.captureMessage(message)
            return self.redirect_to_uploads()
        else:
            return context


# /projects/test-project/1/delete
projects.add_url_rule(
    '/<name>/uploads/<upload_id>/delete',
    view_func=UploadsDeleteView.as_view('delete')
)
# /projects/test-project/1/data
projects.add_url_rule(
    '/<name>/uploads/<upload_id>/formdata',
    view_func=UploadsFormDataView.as_view('formdata')
)
# /projects/test-project/1/download
projects.add_url_rule(
    '/<name>/uploads/<upload_id>/download',
    view_func=UploadsDownloadView.as_view('download')
)
# /projects/test-project/1/release
projects.add_url_rule(
    '/<name>/uploads/<upload_id>/release',
    view_func=UploadsReleaseView.as_view('release')
)
# /projects/test-project
projects.add_url_rule(
    '/<name>/uploads',
    view_func=UploadsView.as_view('uploads'),
)
# /projects/test-project
projects.add_url_rule(
    '/<name>',
    view_func=DetailView.as_view('detail')
)
