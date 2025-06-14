from datetime import datetime
import hashlib
import hmac
import logging
import os
import shutil
import tempfile

import delegator
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    request,
    send_from_directory,
    url_for,
)
from flask.views import MethodView
from flask_login import current_user, login_required

# Use packaging.utils instead of deprecated pkg_resources
from packaging.utils import canonicalize_name as safe_name
from packaging.version import parse as parse_version
import requests
from sqlalchemy import desc, nullsfirst, nullslast
from sqlalchemy.sql.expression import func
from werkzeug.security import safe_join
from werkzeug.utils import secure_filename

from ..account import github
from ..account.forms import LeaveForm
from ..auth import current_user_is_roadie
from ..decorators import templated
from ..exceptions import eject
from ..members.decorators import member_required
from ..tasks import spinach
from .forms import BulkReleaseForm, DeleteForm, ReleaseForm, UploadForm
from .models import Project, ProjectMembership, ProjectUpload
from .tasks import send_new_upload_notifications, update_upload_ordering


projects = Blueprint("projects", __name__, url_prefix="/projects")

logger = logging.getLogger(__name__)

MAX_FILESIZE = 60 * 1024 * 1024  # 60M
MAX_SIGSIZE = 8 * 1024  # 8K
SIGNATURE_START = b"-----BEGIN PGP SIGNATURE-----"
PATH_HASHER = "sha256"
DEFAULT_SORTER = func.random()
SORTERS = {
    "uploads": Project.uploads_count,
    "members": Project.membership_count,
    "watchers": Project.subscribers_count,
    "stargazers": Project.stargazers_count,
    "forks": Project.forks_count,
    "issues": Project.open_issues_count,
    "name": Project.name,
    "random": DEFAULT_SORTER,
}
DEFAULT_ORDER = "desc"


@projects.route("")
@templated()
def index():
    requested_sorter = request.args.get("sorter", None)
    if requested_sorter is None or requested_sorter not in SORTERS:
        sorter = "random"
        initial_sorting = True
    else:
        sorter = requested_sorter
        initial_sorting = False
    criterion = SORTERS.get(sorter, DEFAULT_SORTER)

    order = request.args.get("order", None)
    if order == DEFAULT_ORDER:
        criterion = nullslast(desc(criterion))
    else:
        criterion = nullsfirst(criterion)

    projects = Project.query.filter(Project.is_active.is_(True)).order_by(criterion)
    return {
        "projects": projects,
        "sorter": sorter,
        "initial_sorting": initial_sorting,
        "order": order,
        "DEFAULT_ORDER": DEFAULT_ORDER,
    }


class ProjectMixin:
    def project_query(self, name):
        return Project.query.filter(Project.is_active.is_(True), Project.name == name)

    def project_name(self, *args, **kwargs):
        name = kwargs.get("name")
        if not name:
            abort(404)
        return name

    def redirect_to_project(self):
        return redirect(url_for("projects.detail", name=self.project.name))

    def dispatch_request(self, *args, **kwargs):
        name = self.project_name(*args, **kwargs)
        self.project = self.project_query(name).first_or_404()
        return super().dispatch_request(*args, **kwargs)


class DetailView(ProjectMixin, MethodView):
    """
    A view to show the details of a project.
    """

    methods = ["GET"]
    decorators = [templated()]

    def get(self, name):
        uploads = self.project.uploads.order_by(
            ProjectUpload.ordering.desc(), ProjectUpload.version.desc()
        )
        versions = {upload.version for upload in uploads}
        return {
            "project": self.project,
            "uploads": uploads,
            "versions": sorted(versions, key=parse_version, reverse=True),
        }


class JoinView(ProjectMixin, MethodView):
    """
    A view to show the join a project team.
    """

    methods = ["GET"]
    decorators = [
        member_required(message="You currently can't join this project"),
        login_required,
    ]

    def get(self, name):
        response = github.join_team(self.project.team_slug, current_user.login)
        if response and response.status_code == 200:
            membership = self.project.membership.filter(
                ProjectMembership.user_id == current_user.id,
            ).first()
            if not membership:
                # create a new project membership
                membership = ProjectMembership(
                    user_id=current_user.id, project_id=self.project.id
                )
                membership.save()
            flash(f"You have joined the {self.project.name} team.")
        else:
            flash(f"Something went wrong while joining the {self.project.name} team.")
        return self.redirect_to_project()


class LeaveView(ProjectMixin, MethodView):
    """
    A view to show the join a project team.
    """

    methods = ["GET", "POST"]
    decorators = [member_required(), login_required, templated()]

    def get(self, name):
        if not self.project.user_is_member(current_user):
            flash(f"You're not a member of {self.project.name} at the moment.")
            return self.redirect_to_project()

        return {
            "project": self.project,
            "leave_form": LeaveForm(),
        }

    def post(self, name):
        if not self.project.user_is_member(current_user):
            flash(f"You're not a member of {self.project.name} at the moment.")
            return self.redirect_to_project()

        form = LeaveForm()
        if form.validate_on_submit():
            response = github.leave_team(self.project.team_slug, current_user.login)
            if response and response.status_code == 204:
                membership = self.project.membership.filter(
                    ProjectMembership.user_id == current_user.id,
                ).first()
                if membership:
                    membership.delete()
                flash(
                    f"You have been removed from the {self.project.name} team. "
                    f"See you soon!"
                )
            else:
                flash(
                    f"Leaving the {self.project.name} team failed. "
                    f"Please try again or open a ticket for the roadies."
                )
            return self.redirect_to_project()
        return {
            "project": self.project,
            "leave_form": form,
        }


class UploadView(ProjectMixin, MethodView):
    """
    A view to show the details of a project and also handling file uploads
    via Twine/distutils.
    """

    methods = ["POST"]

    def check_authentication(self):
        """
        Authenticate a request using a database lookup.
        """
        if request.authorization is None:
            return False
        # the upload killswitch
        if not current_app.config["UPLOAD_ENABLED"]:
            return False
        if request.authorization.username != "jazzband":
            return False
        return self.project.credentials.filter_by(
            is_active=True, key=request.authorization.password
        ).scalar()

    def post(self, name):
        if not self.check_authentication():
            response = make_response("", 401)
            response.headers["WWW-Authenticate"] = 'Basic realm="Jazzband"'
            return response

        # distutils "helpfully" substitutes unknown, but "required" values
        # with the string "UNKNOWN". This is basically never what anyone
        # actually wants so we'll just go ahead and delete anything whose
        # value is UNKNOWN.
        form_copy = request.form.copy()
        unknown_found = False
        for key, value in request.form.items():
            if value == "UNKNOWN":
                unknown_found = True
                form_copy.pop(key)
        if unknown_found:
            request.form = form_copy

        form = UploadForm(meta={"csrf": False})

        validation_order = ["name", "version", "content"]
        if not form.validate_on_submit():
            for field_name in validation_order:
                if field_name in form.errors:
                    break
            else:
                field_name = sorted(form.errors.keys())[0]

            eject(
                400,
                description="%s: %s" % (field_name, ", ".join(form.errors[field_name])),
            )

        # the upload FileStorage
        upload_data = form.content.data

        if upload_data is None:
            eject(400, description="Upload payload does not have a file.")

        upload_filename = secure_filename(upload_data.filename)

        # Make sure that our filename matches the project that it is being
        # uploaded to.
        prefix = safe_name(self.project.name).lower()
        if not safe_name(upload_filename).lower().startswith(prefix):
            eject(
                400,
                description="The filename for %r must start with %r."
                % (self.project.name, prefix),
            )

        # Fail if a project upload already exists
        if ProjectUpload.query.filter_by(
            filename=upload_filename, project_id=self.project.id
        ).scalar():
            eject(400, description="File already exists.")

        # Store file uploads and calculate hashes
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_path = os.path.join(tmpdir, upload_filename)
            upload_data.stream.seek(0)
            upload_data.save(upload_path)

            # Buffer the entire file onto disk, checking the hash of the file
            # as we go along.
            with open(upload_path, "rb") as upload_file:
                file_hashes = {
                    "md5": hashlib.md5(),
                    "sha256": hashlib.sha256(),
                    "blake2_256": hashlib.blake2b(digest_size=256 // 8),
                }
                for chunk in iter(lambda: upload_file.read(8096), b""):
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
                    getattr(form, "%s_digest" % digest_name).data.lower(), digest_value
                )
                for digest_name, digest_value in file_hashes.items()
                if getattr(form, "%s_digest" % digest_name).data
            ]
            if not all(hash_comparisons):
                eject(
                    400,
                    description="The digest supplied does not match a digest "
                    "calculated from the uploaded file.",
                )

            # Also buffer the entire signature file to disk.
            signature = form.gpg_signature.data
            signature_filename = upload_filename + ".asc"
            if signature:
                signature_path = os.path.join(tmpdir, signature_filename)
                signature.stream.seek(0)
                signature.save(signature_path)
                if os.path.getsize(signature_path) > MAX_SIGSIZE:
                    eject(400, description="Signature too large.")

                # Check whether signature is ASCII armored
                with open(signature_path, "rb") as signature_file:
                    if not signature_file.read().startswith(SIGNATURE_START):
                        eject(400, description="PGP signature is not ASCII armored.")

            version = form.version.data
            upload = ProjectUpload(
                version=version,
                project=self.project,
                # e.g. acme/2coffee12345678123123123123123123
                path=safe_join(self.project.name, file_hashes[PATH_HASHER]),
                filename=upload_filename,
                size=os.path.getsize(upload_path),
                md5_digest=file_hashes["md5"],
                sha256_digest=file_hashes["sha256"],
                blake2_256_digest=file_hashes["blake2_256"],
                form_data=request.form,
                user_agent=request.user_agent.string,
                remote_addr=request.remote_addr,
            )

            # make the storage path directory /app/uploads/acme
            os.makedirs(os.path.dirname(upload.full_path), exist_ok=True)
            # move the uploaded file to storage path directory
            shutil.move(upload_path, upload.full_path)
            # copy the uploaded signature file to storage path directory
            if signature:
                shutil.move(signature_path, upload.full_path + ".asc")
            # write to database
            upload.save()

        spinach.schedule(send_new_upload_notifications, self.project.id)
        spinach.schedule(update_upload_ordering, self.project.id)
        return "OK"


class UploadActionView(ProjectMixin, MethodView):
    decorators = [login_required]

    def dispatch_request(self, *args, **kwargs):
        name = self.project_name(*args, **kwargs)
        self.project = self.project_query(name).first_or_404()
        self.upload = self.project.uploads.filter_by(
            id=kwargs.get("upload_id")
        ).first_or_404()
        return super().dispatch_request(*args, **kwargs)


class UploadMembersActionView(UploadActionView):
    def project_query(self, name):
        projects = super().project_query(name)
        return projects.filter(Project.membership.any(user=current_user))


class UploadLeadsActionView(UploadMembersActionView):
    def project_query(self, name):
        projects = super().project_query(name)
        if current_user_is_roadie():
            return projects
        return projects.filter(
            Project.membership.any(is_lead=True),
        )


class UploadDownloadView(UploadMembersActionView):
    methods = ["GET"]

    def get(self, name, upload_id):
        max_age = current_app.get_send_file_max_age(self.upload.full_path)
        path, filename = os.path.split(self.upload.full_path)
        return send_from_directory(
            path,
            filename,
            max_age=max_age,
            as_attachment=True,
            download_name=self.upload.filename,
            etag=False,
            conditional=True,
        )


class UploadFormDataView(UploadMembersActionView):
    methods = ["GET"]

    def get(self, name, upload_id):
        return jsonify(self.upload.form_data)


class UploadReleaseView(UploadLeadsActionView):
    methods = ["GET", "POST"]
    decorators = UploadLeadsActionView.decorators + [templated()]

    def validate_upload(self, timeout=10):
        """
        Validate upload against PyPI API.
        Returns (success, errors, warnings) tuple.

        Strategy: Treat CDN propagation delays and temporary network issues as
        warnings rather than blocking errors, while still catching real problems.
        """
        errors = []
        warnings = []

        try:
            # Add timeout to prevent hanging on slow CDN responses
            pypi_response = requests.get(
                self.upload.project.pypi_json_url, timeout=timeout
            )
            pypi_response.raise_for_status()
            data = pypi_response.json()

        except requests.exceptions.Timeout:
            # CDN or network timeout - don't block release
            warning = (
                f"Validation timed out after {timeout}s. This might be due to CDN "
                f"propagation delays. The upload may still be successful."
            )
            logger.warning(warning)
            warnings.append(warning)
            return True, [], warnings

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # File not yet available - likely CDN delay
                warning = (
                    "File not yet visible on PyPI API. This is likely due to CDN "
                    "propagation delays and should resolve shortly."
                )
                logger.warning(warning)
                warnings.append(warning)
                return True, [], warnings
            else:
                # Other HTTP errors are more serious
                error = f"HTTP error {e.response.status_code} while validating upload"
                logger.error(error, exc_info=True)
                errors.append(error)
                return False, errors, warnings

        except requests.exceptions.RequestException:
            # Network issues - don't block release
            warning = (
                "Network error during validation. The upload may still be successful. "
                "Please verify manually on PyPI if needed."
            )
            logger.warning(warning)
            warnings.append(warning)
            return True, [], warnings

        except ValueError:
            # JSON parsing error - this is a real problem
            error = "Error while parsing response from PyPI during validation"
            logger.error(error, exc_info=True)
            errors.append(error)
            return False, errors, warnings

        except Exception:
            # Unknown errors - don't block release but warn
            warning = (
                "Unknown error during validation. The upload may still be successful. "
                "Please verify manually on PyPI if needed."
            )
            logger.warning(warning, exc_info=True)
            warnings.append(warning)
            return True, [], warnings

        # Validation request successful - check the data
        success, validation_errors, validation_warnings = self._validate_upload_data(
            data
        )
        errors.extend(validation_errors)
        warnings.extend(validation_warnings)

        # Return success if no real errors (only allow blocking on hash mismatches)
        return len(errors) == 0, errors, warnings

    def _validate_upload_data(self, data):
        """
        Validate the actual upload data from PyPI.
        Returns (success, errors, warnings) tuple.
        """
        errors = []
        warnings = []

        releases = data.get("releases", {})
        release_files = releases.get(self.upload.version, [])

        if not release_files:
            # No files found - likely CDN delay, treat as warning
            warning = (
                f"No released files found for version {self.upload.version}. "
                f"This might be due to CDN propagation delays."
            )
            warnings.append(warning)
            logger.warning(warning)
            return True, [], warnings

        # Look for our specific file
        found_file = False
        for release_file in release_files:
            release_filename = release_file.get("filename", None)
            if release_filename is None:
                continue

            if release_filename == self.upload.filename:
                found_file = True
                # Validate file hashes - these are REAL errors if they don't match
                digests = release_file.get("digests", {})
                if digests:
                    md5_digest = digests.get("md5", None)
                    if md5_digest and md5_digest != self.upload.md5_digest:
                        error = (
                            f"MD5 hash of {self.upload.filename} does "
                            f"not match hash returned by PyPI."
                        )
                        errors.append(error)
                        logger.error(error, extra={"stack": True})

                    sha256_digest = digests.get("sha256", None)
                    if sha256_digest and sha256_digest != self.upload.sha256_digest:
                        error = (
                            f"SHA256 hash of {self.upload.filename} "
                            f"does not match hash returned by PyPI."
                        )
                        errors.append(error)
                        logger.error(error, extra={"stack": True})
                else:
                    # No digests available - warn but don't block
                    warning = f"No digests available for file {self.upload.filename}"
                    warnings.append(warning)
                    logger.warning(warning)
                break

        if not found_file:
            # File not visible yet - likely CDN delay, treat as warning
            warning = (
                f"File {self.upload.filename} not yet visible in PyPI API. "
                f"This is likely due to CDN propagation delays."
            )
            warnings.append(warning)
            logger.warning(warning)
            return True, [], warnings

        # If we found the file and no hash errors, validation passed
        return len(errors) == 0, errors, warnings

    def post(self, name, upload_id):
        if not current_app.config["RELEASE_ENABLED"]:
            message = "Releasing is currently out of service"
            flash(message)
            logging.info(message)

        if self.upload.released_at:
            flash(
                f"The upload {self.upload.filename} has already been released "
                f"and can't be released again."
            )
            return self.redirect_to_project()

        release_form = ReleaseForm(project_name=self.project.name)

        context = {
            "release_form": release_form,
            "project": self.project,
            "upload": self.upload,
        }

        if release_form.validate_on_submit():
            # copy path to new tmp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                upload_path = os.path.join(tmpdir, self.upload.filename)
                shutil.copy(self.upload.full_path, upload_path)

                # run twine upload against copied upload file
                twine_run = delegator.run(f"twine upload {upload_path}")

            if twine_run.return_code == 0:
                # Validate upload but don't block on warnings
                validation_success, errors, warnings = self.validate_upload()

                # Add errors to form (these will block release)
                if errors:
                    release_form.add_global_error(*errors)

                # Show warnings as flash messages (these won't block)
                for warning in warnings:
                    flash(warning, category="warning")

                # Proceed with release if no blocking errors
                if not errors:
                    # create ProjectRelease object with reference to project
                    self.upload.released_at = datetime.utcnow()
                    # write to database
                    self.upload.save()

                    if warnings:
                        message = (
                            f"You've successfully released {self.upload} to PyPI. "
                            f"Note: Some validation warnings were encountered (see above)."
                        )
                    else:
                        message = f"You've successfully released {self.upload} to PyPI."

                    flash(message, category="success")
                    logger.info(message)
                    return self.redirect_to_project()
            else:
                error = f"Release of {self.upload} failed."
                release_form.add_global_error(error)
                logger.error(
                    error, extra={"data": {"out": twine_run.out, "err": twine_run.err}}
                )
            context.update({"twine_run": twine_run, "upload": self.upload})

        return context

    def get(self, name, upload_id):
        if self.upload.released_at:
            message = (
                f"The upload {self.upload} has already been released "
                f"and can't be released again."
            )
            flash(message)
            logger.info(message)
            return self.redirect_to_project()

        release_form = ReleaseForm(project_name=self.project.name)
        return {
            "project": self.project,
            "release_form": release_form,
            "upload": self.upload,
        }


class UploadDeleteView(UploadLeadsActionView):
    methods = ["GET", "POST"]
    decorators = UploadLeadsActionView.decorators + [templated()]

    def get(self, name, upload_id):
        if self.upload.released_at:
            message = (
                f"The upload {self.upload} has already been "
                f"released and can't be deleted."
            )
            flash(message)
            logger.info(message)
            return self.redirect_to_project()

        return {
            "project": self.project,
            "upload": self.upload,
            "delete_form": DeleteForm(project_name=self.project.name),
        }

    def post(self, name, upload_id):
        if self.upload.released_at:
            message = (
                f"The upload {self.upload} has already been "
                f"released and can't be deleted."
            )
            flash(message)
            logger.error(message, extra={"stack": True})
            return self.redirect_to_project()

        delete_form = DeleteForm(project_name=self.project.name)
        context = {
            "delete_form": delete_form,
            "project": self.project,
            "upload": self.upload,
        }

        if delete_form.validate_on_submit():
            self.upload.delete()
            message = f"You've successfully deleted the upload {self.upload}."
            flash(message)
            logger.info(message)
            return self.redirect_to_project()
        else:
            return context


class BulkReleaseView(ProjectMixin, MethodView):
    """
    A view to release all uploads of a given version at once.
    """

    methods = ["GET", "POST"]
    decorators = [login_required, templated()]

    def project_query(self, name):
        """Override to include authorization logic for project leads."""
        projects = super().project_query(name)
        if current_user_is_roadie():
            return projects
        return projects.filter(
            Project.membership.any(user=current_user, is_lead=True),
        )

    def get_unreleased_uploads_for_version(self, version):
        """Get all unreleased uploads for a specific version."""
        return self.project.uploads.filter_by(version=version, released_at=None).all()

    def validate_uploads_bulk(self, uploads, timeout=10):
        """
        Validate multiple uploads at once.
        Returns (overall_success, all_errors, all_warnings) tuple.
        """
        all_errors = []
        all_warnings = []

        for upload in uploads:
            # Create a temporary UploadReleaseView to use its validation logic
            temp_view = UploadReleaseView()
            temp_view.upload = upload
            temp_view.project = self.project

            success, errors, warnings = temp_view.validate_upload(timeout)

            # Prefix errors/warnings with filename for clarity
            for error in errors:
                all_errors.append(f"{upload.filename}: {error}")
            for warning in warnings:
                all_warnings.append(f"{upload.filename}: {warning}")

        # Overall success if no blocking errors
        return len(all_errors) == 0, all_errors, all_warnings

    def release_uploads_bulk(self, uploads):
        """
        Release multiple uploads using twine.
        Returns (success, twine_outputs) tuple.
        """
        twine_outputs = []

        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy all files to temp directory
            upload_paths = []
            for upload in uploads:
                upload_path = os.path.join(tmpdir, upload.filename)
                shutil.copy(upload.full_path, upload_path)
                upload_paths.append(upload_path)

            # Run twine upload on all files at once
            files_arg = " ".join(f'"{path}"' for path in upload_paths)
            twine_run = delegator.run(f"twine upload {files_arg}")
            twine_outputs.append(twine_run)

        return twine_run.return_code == 0, twine_outputs

    def get(self, name, version):
        if not current_app.config["RELEASE_ENABLED"]:
            message = "Releasing is currently out of service"
            flash(message)
            return self.redirect_to_project()

        uploads = self.get_unreleased_uploads_for_version(version)

        if not uploads:
            flash(f"No unreleased uploads found for version {version}")
            return self.redirect_to_project()

        # Check if any uploads are already released
        released_uploads = (
            self.project.uploads.filter_by(version=version)
            .filter(ProjectUpload.released_at.isnot(None))
            .all()
        )

        bulk_release_form = BulkReleaseForm(project_name=self.project.name)

        return {
            "project": self.project,
            "version": version,
            "uploads": uploads,
            "released_uploads": released_uploads,
            "bulk_release_form": bulk_release_form,
        }

    def post(self, name, version):
        if not current_app.config["RELEASE_ENABLED"]:
            message = "Releasing is currently out of service"
            flash(message)
            return self.redirect_to_project()

        uploads = self.get_unreleased_uploads_for_version(version)

        if not uploads:
            flash(f"No unreleased uploads found for version {version}")
            return self.redirect_to_project()

        bulk_release_form = BulkReleaseForm(project_name=self.project.name)

        context = {
            "project": self.project,
            "version": version,
            "uploads": uploads,
            "bulk_release_form": bulk_release_form,
        }

        if bulk_release_form.validate_on_submit():
            # Validate all uploads first
            validation_success, all_errors, all_warnings = self.validate_uploads_bulk(
                uploads
            )

            # Add validation errors to form (these will block release)
            if all_errors:
                bulk_release_form.add_global_error(*all_errors)

            # Show warnings as flash messages (these won't block)
            for warning in all_warnings:
                flash(warning, category="warning")

            # Proceed with bulk release if no blocking errors
            if not all_errors:
                # Release all uploads at once
                release_success, twine_outputs = self.release_uploads_bulk(uploads)

                if release_success:
                    # Mark all uploads as released
                    release_time = datetime.utcnow()
                    released_count = 0

                    for upload in uploads:
                        upload.released_at = release_time
                        upload.save()
                        released_count += 1

                    if all_warnings:
                        message = (
                            f"Successfully released {released_count} uploads for version {version} to PyPI. "
                            f"Note: Some validation warnings were encountered (see above)."
                        )
                    else:
                        message = f"Successfully released {released_count} uploads for version {version} to PyPI."

                    flash(message, category="success")
                    logger.info(
                        f"Bulk release successful: {released_count} uploads for {self.project.name} v{version}"
                    )
                    return self.redirect_to_project()
                else:
                    error = f"Bulk release of version {version} failed."
                    bulk_release_form.add_global_error(error)
                    logger.error(
                        error,
                        extra={
                            "data": {
                                "twine_outputs": [
                                    output.out for output in twine_outputs
                                ]
                            }
                        },
                    )
                    context.update({"twine_outputs": twine_outputs})

        return context


# /projects/test-project/1/delete
projects.add_url_rule(
    "/<name>/upload/<upload_id>/delete", view_func=UploadDeleteView.as_view("delete")
)
# /projects/test-project/1/data
projects.add_url_rule(
    "/<name>/upload/<upload_id>/formdata",
    view_func=UploadFormDataView.as_view("formdata"),
)
# /projects/test-project/1/download
projects.add_url_rule(
    "/<name>/upload/<upload_id>/download",
    view_func=UploadDownloadView.as_view("download"),
)
# /projects/test-project/1/release
projects.add_url_rule(
    "/<name>/upload/<upload_id>/release", view_func=UploadReleaseView.as_view("release")
)
# /projects/test-project/release/1.0.0
projects.add_url_rule(
    "/<name>/release/<version>", view_func=BulkReleaseView.as_view("bulk_release")
)
# /projects/test-project/join
projects.add_url_rule("/<name>/join", view_func=JoinView.as_view("join"))
# /projects/test-project/leave
projects.add_url_rule("/<name>/leave", view_func=LeaveView.as_view("leave"))
# /projects/test-project/upload
projects.add_url_rule("/<name>/upload", view_func=UploadView.as_view("upload"))
# /projects/test-project
projects.add_url_rule("/<name>", view_func=DetailView.as_view("detail"))
