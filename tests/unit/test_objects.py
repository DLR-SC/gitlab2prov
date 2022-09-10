from datetime import datetime, timedelta
from urllib.parse import urlencode

from prov.model import (
    PROV_TYPE,
    PROV_ROLE,
    PROV_ATTR_STARTTIME,
    PROV_ATTR_ENDTIME,
    PROV_LABEL,
)

from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvType, ProvRole
from gitlab2prov.prov.operations import qualified_name

from tests.random_refs import random_suffix


today = datetime.now()
yesterday = today - timedelta(days=1)
next_week = today + timedelta(days=7)
tomorrow = today + timedelta(days=1)


class TestUser:
    def test_identifier(self):
        name = f"user-name-{random_suffix()}"
        email = f"user-email-{random_suffix()}"
        username = f"user-username-{random_suffix()}"
        id = f"user-id-{random_suffix()}"
        role = ProvRole.AUTHOR
        user = objects.User(
            name=name,
            email=email,
            gitlab_username=username,
            gitlab_id=id,
            prov_role=role,
        )
        expected_identifier = qualified_name(
            f"User?{urlencode([('name', name), ('email', email)])}"
        )
        assert user.prov_identifier == expected_identifier

    def test_attributes(self):
        name = f"user-name-{random_suffix()}"
        email = f"user-email-{random_suffix()}"
        username = f"user-username-{random_suffix()}"
        id = f"user-id-{random_suffix()}"
        role = f"user-prov-role-{random_suffix()}"
        role = ProvRole.AUTHOR
        user = objects.User(
            name=name,
            email=email,
            gitlab_username=username,
            gitlab_id=id,
            prov_role=role,
        )
        expected_attributes = [
            ("name", name),
            ("email", email),
            ("gitlab_username", username),
            ("gitlab_id", id),
            (PROV_ROLE, role),
            (PROV_TYPE, ProvType.USER),
            (PROV_LABEL, user.prov_label),
        ]
        assert user.prov_attributes == expected_attributes

    def test_email_normalization(self):
        name = f"user-name-{random_suffix()}"
        role = f"user-prov-role-{random_suffix()}"
        uppercase = f"user-email-{random_suffix()}".upper()
        user = objects.User(name=name, email=uppercase, prov_role=role)
        assert user.email.islower()


class TestFile:
    def test_identifier(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        f = objects.File(path=path, committed_in=hexsha)
        expected_identifier = qualified_name(
            f"File?{urlencode([('path', path), ('committed_in', hexsha)])}"
        )
        assert f.prov_identifier == expected_identifier

    def test_attributes(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        f = objects.File(path=path, committed_in=hexsha)
        expected_attributes = [
            ("path", path),
            ("committed_in", hexsha),
            (PROV_TYPE, ProvType.FILE),
            (PROV_LABEL, f.prov_label),
        ]
        assert f.prov_attributes == expected_attributes


class TestFileRevision:
    def test_identifier(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        change_type = f"change-type-{random_suffix()}"
        file_revision = objects.FileRevision(
            path=path,
            committed_in=hexsha,
            change_type=change_type,
            original=None,
            previous=None,
        )
        expected_identifier = qualified_name(
            f"FileRevision?{urlencode([('path', path), ('committed_in', hexsha), ('change_type', change_type)])}"
        )
        assert file_revision.prov_identifier == expected_identifier

    def test_attributes(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        change_type = f"change-type-{random_suffix()}"
        file_revision = objects.FileRevision(
            path=path,
            committed_in=hexsha,
            change_type=change_type,
            original=None,
            previous=None,
        )
        expected_attributes = [
            ("path", path),
            ("committed_in", hexsha),
            ("change_type", change_type),
            (PROV_TYPE, ProvType.FILE_REVISION),
            (PROV_LABEL, file_revision.prov_label),
        ]
        assert file_revision.prov_attributes == expected_attributes


class TestGitCommit:
    def test_identifier(self):
        hexsha = f"commit-hash-{random_suffix()}"
        msg = f"commit-message-{random_suffix()}"
        title = f"commit-title-{random_suffix()}"
        commit = objects.GitCommit(
            hexsha=hexsha,
            message=msg,
            title=title,
            author=None,
            committer=None,
            parents=[],
            prov_start=today,
            prov_end=tomorrow,
        )
        expected_identifier = qualified_name(
            f"GitCommit?{urlencode([('hexsha', hexsha)])}"
        )
        assert commit.prov_identifier == expected_identifier

    def test_attributes(self):
        hexsha = f"commit-hash-{random_suffix()}"
        msg = f"commit-message-{random_suffix()}"
        title = f"commit-title-{random_suffix()}"
        commit = objects.GitCommit(
            hexsha=hexsha,
            message=msg,
            title=title,
            author=None,
            committer=None,
            parents=[],
            prov_start=today,
            prov_end=tomorrow,
        )
        expected_attributes = [
            ("hexsha", hexsha),
            ("message", msg),
            ("title", title),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, ProvType.GIT_COMMIT),
            (PROV_LABEL, commit.prov_label),
        ]
        assert commit.prov_attributes == expected_attributes


class TestAsset:
    def test_identifier(self):
        url = f"asset-url-{random_suffix()}"
        fmt = f"asset-format-{random_suffix()}"
        asset = objects.Asset(url=url, format=fmt)
        expected_identifier = qualified_name(
            f"Asset?{urlencode([('url', url), ('format', fmt)])}"
        )
        assert asset.prov_identifier == expected_identifier

    def test_attributes(self):
        url = f"asset-url-{random_suffix()}"
        fmt = f"asset-format-{random_suffix()}"
        asset = objects.Asset(url=url, format=fmt)
        expected_attributes = [
            ("url", url),
            ("format", fmt),
            (PROV_TYPE, ProvType.ASSET),
            (PROV_LABEL, asset.prov_label),
        ]
        assert asset.prov_attributes == expected_attributes


class TestEvidence:
    def test_identifier(self):
        sha = f"evidence-sha-{random_suffix()}"
        url = f"evidence-url-{random_suffix()}"
        evidence = objects.Evidence(hexsha=sha, url=url, collected_at=today)
        expected_identifier = qualified_name(
            f"Evidence?{urlencode([('hexsha', sha), ('url', url), ('collected_at', today)])}"
        )
        assert evidence.prov_identifier == expected_identifier

    def test_attributes(self):
        sha = f"evidence-sha-{random_suffix()}"
        url = f"evidence-url-{random_suffix()}"
        evidence = objects.Evidence(hexsha=sha, url=url, collected_at=today)
        expected_attributes = [
            ("hexsha", sha),
            ("url", url),
            ("collected_at", today),
            (PROV_TYPE, ProvType.EVIDENCE),
            (PROV_LABEL, evidence.prov_label),
        ]
        assert evidence.prov_attributes == expected_attributes


class TestAnnotatedVersion:
    def test_identifier(self):
        vid = f"version-id-{random_suffix()}"
        aid = f"annotation-id-{random_suffix()}"
        annotated_version = objects.AnnotatedVersion(
            version_id=vid,
            annotation_id=aid,
            prov_type=ProvType.GITLAB_COMMIT_VERSION_ANNOTATED,
        )
        expected_identifier = qualified_name(
            f"{ProvType.GITLAB_COMMIT_VERSION_ANNOTATED}?{urlencode([('version_id', vid), ('annotation_id', aid)])}"
        )
        assert annotated_version.prov_identifier == expected_identifier

    def test_attributes(self):
        vid = f"version-id-{random_suffix()}"
        aid = f"annotation-id-{random_suffix()}"
        annotated_version = objects.AnnotatedVersion(
            version_id=vid, annotation_id=aid, prov_type="TestAnnotatedVersion"
        )
        expected_attributes = [
            ("version_id", vid),
            ("annotation_id", aid),
            (PROV_TYPE, "TestAnnotatedVersion"),
            (PROV_LABEL, annotated_version.prov_label),
        ]
        assert annotated_version.prov_attributes == expected_attributes


class TestCreation:
    def test_identifier(self):
        id = f"creation-id-{random_suffix()}"
        creation = objects.Creation(
            creation_id=id,
            prov_start=today,
            prov_end=tomorrow,
            prov_type=ProvType.TAG_CREATION,
        )
        expected_identifier = qualified_name(
            f"{ProvType.TAG_CREATION}?{urlencode([('creation_id', id)])}"
        )
        assert creation.prov_identifier == expected_identifier

    def test_attributes(self):
        id = f"creation-id-{random_suffix()}"
        creation = objects.Creation(
            creation_id=id,
            prov_start=today,
            prov_end=tomorrow,
            prov_type=ProvType.TAG_CREATION,
        )
        expected_attributes = [
            ("creation_id", id),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, "TagCreation"),
            (PROV_LABEL, creation.prov_label),
        ]
        assert creation.prov_attributes == expected_attributes


class TestAnnotation:
    def test_identifier(self):
        id = f"annotation-id-{random_suffix()}"
        type = f"annotation-type-{random_suffix()}"
        body = f"annotation-body-{random_suffix()}"
        annotation = objects.Annotation(
            id=id,
            type=type,
            body=body,
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        expected_identifier = qualified_name(
            f"Annotation?{urlencode([('id', id), ('type', type)])}"
        )
        assert annotation.prov_identifier == expected_identifier

    def test_attributes(self):
        id = f"annotation-id-{random_suffix()}"
        type = f"annotation-type-{random_suffix()}"
        body = f"annotation-body-{random_suffix()}"
        annotation = objects.Annotation(
            id=id,
            type=type,
            body=body,
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        expected_attributes = [
            ("id", id),
            ("type", type),
            ("body", body),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, ProvType.ANNOTATION),
            (PROV_LABEL, annotation.prov_label),
        ]
        assert annotation.prov_attributes == expected_attributes

    def test_kwargs(self):
        id = f"annotation-id-{random_suffix()}"
        type = f"annotation-type-{random_suffix()}"
        body = f"annotation-body-{random_suffix()}"
        kwargs = {"kwarg1": "value1", "kwarg2": "value2"}
        annotation = objects.Annotation(
            id=id,
            type=type,
            body=body,
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
            kwargs=kwargs,
        )
        expected_attributes = [
            ("id", id),
            ("type", type),
            ("body", body),
            ("kwarg1", "value1"),
            ("kwarg2", "value2"),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, ProvType.ANNOTATION),
            (PROV_LABEL, annotation.prov_label),
        ]
        assert annotation.prov_attributes == expected_attributes


class TestIssue:
    def test_identifier(self):
        id = f"issue-id-{random_suffix()}"
        iid = f"issue-iid-{random_suffix()}"
        title = f"issue-title-{random_suffix()}"
        desc = f"issue-description-{random_suffix()}"
        url = f"issue-url-{random_suffix()}"
        issue = objects.Issue(
            id=id,
            iid=iid,
            title=title,
            description=desc,
            url=url,
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
        )
        expected_identifier = qualified_name(
            f"Issue?{urlencode([('id', id), ('iid', iid), ('title', title)])}"
        )
        assert issue.prov_identifier == expected_identifier

    def test_attributes(self):
        id = f"issue-id-{random_suffix()}"
        iid = f"issue-iid-{random_suffix()}"
        title = f"issue-title-{random_suffix()}"
        desc = f"issue-description-{random_suffix()}"
        url = f"issue-url-{random_suffix()}"
        issue = objects.Issue(
            id=id,
            iid=iid,
            title=title,
            description=desc,
            url=url,
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
        )
        expected_attributes = [
            ("id", id),
            ("iid", iid),
            ("title", title),
            ("description", desc),
            ("url", url),
            ("created_at", today),
            ("closed_at", tomorrow),
            (PROV_TYPE, ProvType.ISSUE),
            (PROV_LABEL, issue.prov_label),
        ]
        assert issue.prov_attributes == expected_attributes

    def test_creation(self):
        id = f"issue-id-{random_suffix()}"
        issue = objects.Issue(
            id=id,
            iid="",
            title="",
            description="",
            url="",
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
        )
        expected_creation = objects.Creation(
            creation_id=id,
            prov_start=today,
            prov_end=tomorrow,
            prov_type=ProvType.ISSUE_CREATION,
        )
        assert issue.creation == expected_creation

    def test_first_version(self):
        id = f"issue-id-{random_suffix()}"
        issue = objects.Issue(
            id=id,
            iid="",
            title="",
            description="",
            url="",
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
        )
        expected_first_version = objects.Version(
            version_id=id, prov_type=ProvType.ISSUE_VERSION
        )
        assert issue.first_version == expected_first_version

    def test_annotated_versions(self):
        hexsha = f"commit-sha-{random_suffix()}"
        aid1 = f"annotation-id-{random_suffix()}"
        aid2 = f"annotation-id-{random_suffix()}"
        annot1 = objects.Annotation(
            id=aid1,
            type="",
            body="",
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        annot2 = objects.Annotation(
            id=aid2,
            type="",
            body="",
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        annots = [annot1, annot2]
        commit = objects.GitlabCommit(
            hexsha=hexsha,
            url="",
            author=None,
            annotations=annots,
            authored_at=today,
            committed_at=tomorrow,
        )
        ver1 = objects.AnnotatedVersion(
            version_id=hexsha,
            annotation_id=annot1.id,
            prov_type=ProvType.GITLAB_COMMIT_VERSION_ANNOTATED,
        )
        ver2 = objects.AnnotatedVersion(
            version_id=hexsha,
            annotation_id=annot2.id,
            prov_type=ProvType.GITLAB_COMMIT_VERSION_ANNOTATED,
        )
        expected_versions = [ver1, ver2]
        assert commit.annotated_versions == expected_versions


class TestGitlabCommit:
    def test_identifier(self):
        hexsha = f"commit-hash-{random_suffix()}"
        url = f"commit-url-{random_suffix()}"
        commit = objects.GitlabCommit(
            hexsha=hexsha,
            url=url,
            author=None,
            annotations=[],
            authored_at=today,
            committed_at=tomorrow,
        )
        expected_identifier = qualified_name(
            f"GitlabCommit?{urlencode([('hexsha', hexsha)])}"
        )
        assert commit.prov_identifier == expected_identifier

    def test_attributes(self):
        hexsha = f"commit-hash-{random_suffix()}"
        url = f"commit-url-{random_suffix()}"
        commit = objects.GitlabCommit(
            hexsha=hexsha,
            url=url,
            author=None,
            annotations=[],
            authored_at=today,
            committed_at=tomorrow,
        )
        expected_attributes = [
            ("hexsha", hexsha),
            ("url", url),
            ("authored_at", today),
            ("committed_at", tomorrow),
            (PROV_TYPE, ProvType.GITLAB_COMMIT),
            (PROV_LABEL, commit.prov_label),
        ]
        assert commit.prov_attributes == expected_attributes

    def test_creation(self):
        hexsha = f"commit-sha-{random_suffix()}"
        commit = objects.GitlabCommit(
            hexsha=hexsha,
            url="",
            author=None,
            annotations=[],
            authored_at=today,
            committed_at=tomorrow,
        )
        expected_creation = objects.Creation(
            creation_id=hexsha,
            prov_start=today,
            prov_end=tomorrow,
            prov_type=ProvType.GITLAB_COMMIT_CREATION,
        )
        assert commit.creation == expected_creation

    def test_first_version(self):
        hexsha = f"commit-sha-{random_suffix()}"
        commit = objects.GitlabCommit(
            hexsha=hexsha,
            url="",
            author=None,
            annotations=[],
            authored_at=today,
            committed_at=tomorrow,
        )
        expected_first_version = objects.Version(
            version_id=hexsha, prov_type=ProvType.GITLAB_COMMIT_VERSION
        )
        assert commit.first_version == expected_first_version

    def test_annotated_versions(self):
        hexsha = f"commit-sha-{random_suffix()}"
        aid1 = f"annotation-id-{random_suffix()}"
        aid2 = f"annotation-id-{random_suffix()}"
        annot1 = objects.Annotation(
            id=aid1,
            type="",
            body="",
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        annot2 = objects.Annotation(
            id=aid2,
            type="",
            body="",
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        annots = [annot1, annot2]
        commit = objects.GitlabCommit(
            hexsha=hexsha,
            url="",
            author=None,
            annotations=annots,
            authored_at=today,
            committed_at=tomorrow,
        )
        ver1 = objects.AnnotatedVersion(
            version_id=hexsha,
            annotation_id=annot1.id,
            prov_type=ProvType.GITLAB_COMMIT_VERSION_ANNOTATED,
        )
        ver2 = objects.AnnotatedVersion(
            version_id=hexsha,
            annotation_id=annot2.id,
            prov_type=ProvType.GITLAB_COMMIT_VERSION_ANNOTATED,
        )
        expected_versions = [ver1, ver2]
        assert commit.annotated_versions == expected_versions


class TestMergeRequest:
    def test_identifier(self):
        id = f"merge-request-id-{random_suffix()}"
        iid = f"merge-request-iid-{random_suffix()}"
        title = f"merge-request-title-{random_suffix()}"
        desc = f"merge-request-description-{random_suffix()}"
        url = f"merge-request-url-{random_suffix()}"
        source_branch = f"merge-request-source-branch-{random_suffix()}"
        target_branch = f"merge-request-target-branch-{random_suffix()}"
        merge_request = objects.MergeRequest(
            id=id,
            iid=iid,
            title=title,
            description=desc,
            url=url,
            source_branch=source_branch,
            target_branch=target_branch,
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
            merged_at=next_week,
            first_deployed_to_production_at=yesterday,
        )
        expected_identifier = qualified_name(
            f"MergeRequest?{urlencode([('id', id), ('iid', iid), ('title', title)])}"
        )
        assert merge_request.prov_identifier == expected_identifier

    def test_attributes(self):
        id = f"merge-request-id-{random_suffix()}"
        iid = f"merge-request-iid-{random_suffix()}"
        title = f"merge-request-title-{random_suffix()}"
        desc = f"merge-request-description-{random_suffix()}"
        url = f"merge-request-url-{random_suffix()}"
        source_branch = f"merge-request-source-branch-{random_suffix()}"
        target_branch = f"merge-request-target-branch-{random_suffix()}"
        merge_request = objects.MergeRequest(
            id=id,
            iid=iid,
            title=title,
            description=desc,
            url=url,
            source_branch=source_branch,
            target_branch=target_branch,
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
            merged_at=next_week,
            first_deployed_to_production_at=yesterday,
        )
        expected_attributes = [
            ("id", id),
            ("iid", iid),
            ("title", title),
            ("description", desc),
            ("url", url),
            ("source_branch", source_branch),
            ("target_branch", target_branch),
            ("created_at", today),
            ("closed_at", tomorrow),
            ("merged_at", next_week),
            ("first_deployed_to_production_at", yesterday),
            (PROV_TYPE, ProvType.MERGE_REQUEST),
            (PROV_LABEL, merge_request.prov_label),
        ]
        assert merge_request.prov_attributes == expected_attributes

    def test_creation(self):
        id = f"merge-request-id-{random_suffix()}"
        merge_request = objects.MergeRequest(
            id=id,
            iid="",
            title="",
            description="",
            url="",
            source_branch="",
            target_branch="",
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
            merged_at=yesterday,
            first_deployed_to_production_at=next_week,
        )
        expected_creation = objects.Creation(
            creation_id=id,
            prov_start=today,
            prov_end=tomorrow,
            prov_type=ProvType.MERGE_REQUEST_CREATION,
        )
        assert merge_request.creation == expected_creation

    def test_first_version(self):
        id = f"merge-request-id-{random_suffix()}"
        merge_request = objects.MergeRequest(
            id=id,
            iid="",
            title="",
            description="",
            url="",
            source_branch="",
            target_branch="",
            author=None,
            annotations=[],
            created_at=today,
            closed_at=tomorrow,
            merged_at=yesterday,
            first_deployed_to_production_at=next_week,
        )
        expected_version = objects.Version(
            version_id=id, prov_type=ProvType.MERGE_REQUEST_VERSION
        )
        assert merge_request.first_version == expected_version

    def test_annotated_versions(self):
        id = f"merge-request-id-{random_suffix()}"
        aid1 = f"annotation-id-{random_suffix()}"
        aid2 = f"annotation-id-{random_suffix()}"
        annot1 = objects.Annotation(
            id=aid1,
            type="",
            body="",
            kwargs=None,
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        annot2 = objects.Annotation(
            id=aid2,
            type="",
            body="",
            kwargs=None,
            annotator=None,
            prov_start=today,
            prov_end=tomorrow,
        )
        annots = [annot1, annot2]
        merge_request = objects.MergeRequest(
            id=id,
            iid="",
            title="",
            description="",
            url="",
            source_branch="",
            target_branch="",
            author=None,
            annotations=annots,
            created_at=today,
            closed_at=tomorrow,
            merged_at=yesterday,
            first_deployed_to_production_at=next_week,
        )
        ver1 = objects.AnnotatedVersion(
            version_id=id,
            annotation_id=annot1.id,
            prov_type=ProvType.MERGE_REQUEST_VERSION_ANNOTATED,
        )
        ver2 = objects.AnnotatedVersion(
            version_id=id,
            annotation_id=annot2.id,
            prov_type=ProvType.MERGE_REQUEST_VERSION_ANNOTATED,
        )
        expected_versions = [ver1, ver2]
        assert merge_request.annotated_versions == expected_versions


class TestTag:
    def test_identifier(self):
        name = f"tag-name-{random_suffix()}"
        hexsha = f"commit-sha-{random_suffix()}"
        msg = f"tag-message-{random_suffix()}"
        tag = objects.Tag(
            name=name, hexsha=hexsha, message=msg, author=None, created_at=today
        )
        expected_identifier = qualified_name(
            f"Tag?{urlencode([('name', name), ('hexsha', hexsha)])}"
        )
        assert tag.prov_identifier == expected_identifier

    def test_attributes(self):
        name = f"tag-name-{random_suffix()}"
        hexsha = f"commit-sha-{random_suffix()}"
        msg = f"tag-message-{random_suffix()}"
        tag = objects.Tag(
            name=name, hexsha=hexsha, message=msg, author=None, created_at=today
        )
        expected_attributes = [
            ("name", name),
            ("hexsha", hexsha),
            ("message", msg),
            ("created_at", today),
            (PROV_TYPE, ProvType.TAG),
            (PROV_TYPE, ProvType.COLLECTION),
            (PROV_LABEL, tag.prov_label),
        ]
        assert tag.prov_attributes == expected_attributes

    def test_creation(self):
        name = f"tag-name-{random_suffix()}"
        tag = objects.Tag(
            name=name, hexsha="", message="", author=None, created_at=today
        )
        expected_creation = objects.Creation(
            creation_id=name,
            prov_start=today,
            prov_end=today,
            prov_type=ProvType.TAG_CREATION,
        )
        assert tag.creation == expected_creation


class TestRelease:
    def test_identifier(self):
        name = f"release-name-{random_suffix()}"
        desc = f"release-description-{random_suffix()}"
        tag_name = f"tag-name-{random_suffix()}"
        release = objects.Release(
            name=name,
            description=desc,
            tag_name=tag_name,
            author=None,
            assets=[],
            evidences=[],
            created_at=today,
            released_at=tomorrow,
        )
        expected_identifier = qualified_name(f"Release?{urlencode([('name', name)])}")
        assert release.prov_identifier == expected_identifier

    def test_attributes(self):
        name = f"release-name-{random_suffix()}"
        desc = f"release-description-{random_suffix()}"
        tag_name = f"tag-name-{random_suffix()}"
        release = objects.Release(
            name=name,
            description=desc,
            tag_name=tag_name,
            author=None,
            assets=[],
            evidences=[],
            created_at=today,
            released_at=tomorrow,
        )
        expected_attributes = [
            ("name", name),
            ("description", desc),
            ("tag_name", tag_name),
            ("created_at", today),
            ("released_at", tomorrow),
            (PROV_TYPE, ProvType.RELEASE),
            (PROV_TYPE, ProvType.COLLECTION),
            (PROV_LABEL, release.prov_label),
        ]
        assert release.prov_attributes == expected_attributes

    def test_creation(self):
        name = f"release-name-{random_suffix()}"
        release = objects.Release(
            name=name,
            description="",
            tag_name="",
            author=None,
            assets=[],
            evidences=[],
            created_at=today,
            released_at=tomorrow,
        )
        expected_creation = objects.Creation(
            creation_id=name,
            prov_start=today,
            prov_end=tomorrow,
            prov_type=ProvType.RELEASE_CREATION,
        )
        assert release.creation == expected_creation
