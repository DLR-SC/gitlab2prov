from datetime import datetime, timedelta
from urllib.parse import urlencode

from prov.model import PROV_TYPE, PROV_ROLE, PROV_ATTR_STARTTIME, PROV_ATTR_ENDTIME

from gitlab2prov.domain import objects
from gitlab2prov.domain.constants import ProvType
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
        role = f"user-prov-role-{random_suffix()}"
        user = objects.User(name, email, username, id, role)
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
        user = objects.User(name, email, username, id, role)
        expected_attributes = [
            ("name", name),
            ("email", email),
            ("gitlab_username", username),
            ("gitlab_id", id),
            (PROV_ROLE, role),
            (PROV_TYPE, ProvType.User),
        ]
        assert user.prov_attributes == expected_attributes

    def test_email_normalization(self):
        name = f"user-name-{random_suffix()}"
        role = f"user-prov-role-{random_suffix()}"
        uppercase = f"user-email-{random_suffix()}".upper()
        user = objects.User(name, uppercase, prov_role=role)
        assert user.email.islower()


class TestFile:
    def test_identifier(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        f = objects.File(path, hexsha)
        expected_identifier = qualified_name(
            f"File?{urlencode([('path', path), ('commit_hexsha', hexsha)])}"
        )
        assert f.prov_identifier == expected_identifier

    def test_attributes(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        f = objects.File(path, hexsha)
        expected_attributes = [
            ("path", path),
            ("commit_hexsha", hexsha),
            (PROV_TYPE, ProvType.File),
        ]
        assert f.prov_attributes == expected_attributes


class TestFileRevision:
    def test_identifier(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        change_type = f"change-type-{random_suffix()}"
        file_revision = objects.FileRevision(path, hexsha, change_type, None, None)
        expected_identifier = qualified_name(
            f"FileRevision?{urlencode([('path', path), ('commit_hexsha', hexsha), ('change_type', change_type)])}"
        )
        assert file_revision.prov_identifier == expected_identifier

    def test_attributes(self):
        path = f"file-path-{random_suffix()}"
        hexsha = f"commit-hash-{random_suffix()}"
        change_type = f"change-type-{random_suffix()}"
        file_revision = objects.FileRevision(path, hexsha, change_type, None, None)
        expected_attributes = [
            ("path", path),
            ("commit_hexsha", hexsha),
            ("change_type", change_type),
            (PROV_TYPE, ProvType.FileRevision),
        ]
        assert file_revision.prov_attributes == expected_attributes


class TestGitCommit:
    def test_identifier(self):
        hexsha = f"commit-hash-{random_suffix()}"
        msg = f"commit-message-{random_suffix()}"
        title = f"commit-title-{random_suffix()}"
        commit = objects.GitCommit(hexsha, msg, title, None, None, [], today, tomorrow)
        expected_identifier = qualified_name(
            f"GitCommit?{urlencode([('hexsha', hexsha)])}"
        )
        assert commit.prov_identifier == expected_identifier

    def test_attributes(self):
        hexsha = f"commit-hash-{random_suffix()}"
        msg = f"commit-message-{random_suffix()}"
        title = f"commit-title-{random_suffix()}"
        commit = objects.GitCommit(hexsha, msg, title, None, None, [], today, tomorrow)
        expected_attributes = [
            ("hexsha", hexsha),
            ("message", msg),
            ("title", title),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, ProvType.GitCommit),
        ]
        assert commit.prov_attributes == expected_attributes


class TestAsset:
    def test_identifier(self):
        url = f"asset-url-{random_suffix()}"
        fmt = f"asset-format-{random_suffix()}"
        asset = objects.Asset(url, fmt)
        expected_identifier = qualified_name(
            f"Asset?{urlencode([('url', url), ('format', fmt)])}"
        )
        assert asset.prov_identifier == expected_identifier

    def test_attributes(self):
        url = f"asset-url-{random_suffix()}"
        fmt = f"asset-format-{random_suffix()}"
        asset = objects.Asset(url, fmt)
        expected_attributes = [
            ("url", url),
            ("format", fmt),
            (PROV_TYPE, ProvType.Asset),
        ]
        assert asset.prov_attributes == expected_attributes


class TestEvidence:
    def test_identifier(self):
        sha = f"evidence-sha-{random_suffix()}"
        url = f"evidence-url-{random_suffix()}"
        evidence = objects.Evidence(sha, url, today)
        expected_identifier = qualified_name(
            f"Evidence?{urlencode([('hexsha', sha), ('url', url), ('collected_at', today)])}"
        )
        assert evidence.prov_identifier == expected_identifier

    def test_attributes(self):
        sha = f"evidence-sha-{random_suffix()}"
        url = f"evidence-url-{random_suffix()}"
        evidence = objects.Evidence(sha, url, today)
        expected_attributes = [
            ("hexsha", sha),
            ("url", url),
            ("collected_at", today),
            (PROV_TYPE, ProvType.Evidence),
        ]
        assert evidence.prov_attributes == expected_attributes


class TestAnnotatedVersion:
    def test_identifier(self):
        vid = f"version-id-{random_suffix()}"
        aid = f"annotation-id-{random_suffix()}"
        annotated_version = objects.AnnotatedVersion(vid, aid, "TestAnnotatedVersion")
        expected_identifier = qualified_name(
            f"TestAnnotatedVersion?{urlencode([('version_id', vid), ('annotation_id', aid)])}"
        )
        assert annotated_version.prov_identifier == expected_identifier

    def test_attributes(self):
        vid = f"version-id-{random_suffix()}"
        aid = f"annotation-id-{random_suffix()}"
        annotated_version = objects.AnnotatedVersion(vid, aid, "TestAnnotatedVersion")
        expected_attributes = [
            ("version_id", vid),
            ("annotation_id", aid),
            (PROV_TYPE, "TestAnnotatedVersion"),
        ]
        assert annotated_version.prov_attributes == expected_attributes


class TestCreation:
    def test_identifier(self):
        id = f"creation-id-{random_suffix()}"
        creation = objects.Creation(id, today, tomorrow, "TestCreation")
        expected_identifier = qualified_name(
            f"TestCreation?{urlencode([('creation_id', id)])}"
        )
        assert creation.prov_identifier == expected_identifier

    def test_attributes(self):
        id = f"creation-id-{random_suffix()}"
        creation = objects.Creation(id, today, tomorrow, "TestCreation")
        expected_attributes = [
            ("creation_id", id),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, "TestCreation"),
        ]
        assert creation.prov_attributes == expected_attributes


class TestAnnotation:
    def test_identifier(self):
        id = f"annotation-id-{random_suffix()}"
        type = f"annotation-type-{random_suffix()}"
        body = f"annotation-body-{random_suffix()}"
        annotation = objects.Annotation(id, type, body, None, today, tomorrow)
        expected_identifier = qualified_name(
            f"Annotation?{urlencode([('id', id), ('type', type)])}"
        )
        assert annotation.prov_identifier == expected_identifier

    def test_attributes(self):
        id = f"annotation-id-{random_suffix()}"
        type = f"annotation-type-{random_suffix()}"
        body = f"annotation-body-{random_suffix()}"
        annotation = objects.Annotation(id, type, body, None, today, tomorrow)
        expected_attributes = [
            ("id", id),
            ("type", type),
            ("body", body),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, ProvType.Annotation),
        ]
        assert annotation.prov_attributes == expected_attributes

    def test_kwargs(self):
        id = f"annotation-id-{random_suffix()}"
        type = f"annotation-type-{random_suffix()}"
        body = f"annotation-body-{random_suffix()}"
        kwargs = {"kwarg1": "value1", "kwarg2": "value2"}
        annotation = objects.Annotation(id, type, body, None, today, tomorrow, kwargs)
        expected_attributes = [
            ("id", id),
            ("type", type),
            ("body", body),
            (PROV_ATTR_STARTTIME, today),
            (PROV_ATTR_ENDTIME, tomorrow),
            (PROV_TYPE, ProvType.Annotation),
            ("kwarg1", "value1"),
            ("kwarg2", "value2"),
        ]
        assert annotation.prov_attributes == expected_attributes


class TestIssue:
    def test_identifier(self):
        id = f"issue-id-{random_suffix()}"
        iid = f"issue-iid-{random_suffix()}"
        title = f"issue-title-{random_suffix()}"
        desc = f"issue-description-{random_suffix()}"
        url = f"issue-url-{random_suffix()}"
        issue = objects.Issue(id, iid, title, desc, url, None, [], today, tomorrow)
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
        issue = objects.Issue(id, iid, title, desc, url, None, [], today, tomorrow)
        expected_attributes = [
            ("id", id),
            ("iid", iid),
            ("title", title),
            ("description", desc),
            ("url", url),
            ("created_at", today),
            ("closed_at", tomorrow),
            (PROV_TYPE, ProvType.Issue),
        ]
        assert issue.prov_attributes == expected_attributes

    def test_creation(self):
        id = f"issue-id-{random_suffix()}"
        issue = objects.Issue(id, "", "", "", "", None, [], today, tomorrow)
        expected_creation = objects.Creation(
            id, today, tomorrow, ProvType.IssueCreation
        )
        assert issue.creation == expected_creation

    def test_first_version(self):
        id = f"issue-id-{random_suffix()}"
        issue = objects.Issue(id, "", "", "", "", None, [], today)
        expected_first_version = objects.Version(id, ProvType.IssueVersion)
        assert issue.first_version == expected_first_version

    def test_annotated_versions(self):
        hexsha = f"commit-sha-{random_suffix()}"
        aid1 = f"annotation-id-{random_suffix()}"
        aid2 = f"annotation-id-{random_suffix()}"
        annot1 = objects.Annotation(aid1, "", "", None, today, tomorrow)
        annot2 = objects.Annotation(aid2, "", "", None, today, tomorrow)
        annots = [annot1, annot2]
        commit = objects.GitlabCommit(hexsha, "", None, annots, today, tomorrow)
        ver1 = objects.AnnotatedVersion(
            hexsha, annot1.id, ProvType.AnnotatedGitlabCommitVersion
        )
        ver2 = objects.AnnotatedVersion(
            hexsha, annot2.id, ProvType.AnnotatedGitlabCommitVersion
        )
        expected_versions = [ver1, ver2]
        assert commit.annotated_versions == expected_versions


class TestGitlabCommit:
    def test_identifier(self):
        hexsha = f"commit-hash-{random_suffix()}"
        url = f"commit-url-{random_suffix()}"
        commit = objects.GitlabCommit(hexsha, url, None, [], today, tomorrow)
        expected_identifier = qualified_name(
            f"GitlabCommit?{urlencode([('hexsha', hexsha), ('url', url)])}"
        )
        assert commit.prov_identifier == expected_identifier

    def test_attributes(self):
        hexsha = f"commit-hash-{random_suffix()}"
        url = f"commit-url-{random_suffix()}"
        commit = objects.GitlabCommit(hexsha, url, None, [], today, tomorrow)
        expected_attributes = [
            ("hexsha", hexsha),
            ("url", url),
            ("authored_at", today),
            ("committed_at", tomorrow),
            (PROV_TYPE, ProvType.GitlabCommit),
        ]
        assert commit.prov_attributes == expected_attributes

    def test_creation(self):
        hexsha = f"commit-sha-{random_suffix()}"
        commit = objects.GitlabCommit(hexsha, "", None, [], today, tomorrow)
        expected_creation = objects.Creation(
            hexsha, today, tomorrow, ProvType.GitlabCommitCreation
        )
        assert commit.creation == expected_creation

    def test_first_version(self):
        hexsha = f"commit-sha-{random_suffix()}"
        commit = objects.GitlabCommit(hexsha, "", None, [], today, tomorrow)
        expected_first_version = objects.Version(hexsha, ProvType.GitlabCommitVersion)
        assert commit.first_version == expected_first_version

    def test_annotated_versions(self):
        hexsha = f"commit-sha-{random_suffix()}"
        aid1 = f"annotation-id-{random_suffix()}"
        aid2 = f"annotation-id-{random_suffix()}"
        annot1 = objects.Annotation(aid1, "", "", None, today, tomorrow)
        annot2 = objects.Annotation(aid2, "", "", None, today, tomorrow)
        annots = [annot1, annot2]
        commit = objects.GitlabCommit(hexsha, "", None, annots, today, tomorrow)
        ver1 = objects.AnnotatedVersion(
            hexsha, annot1.id, ProvType.AnnotatedGitlabCommitVersion
        )
        ver2 = objects.AnnotatedVersion(
            hexsha, annot2.id, ProvType.AnnotatedGitlabCommitVersion
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
            id,
            iid,
            title,
            desc,
            url,
            source_branch,
            target_branch,
            None,
            [],
            today,
            tomorrow,
            next_week,
            yesterday,
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
            id,
            iid,
            title,
            desc,
            url,
            source_branch,
            target_branch,
            None,
            [],
            today,
            tomorrow,
            next_week,
            yesterday,
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
            (PROV_TYPE, ProvType.MergeRequest),
        ]
        assert merge_request.prov_attributes == expected_attributes

    def test_creation(self):
        id = f"merge-request-id-{random_suffix()}"
        merge_request = objects.MergeRequest(
            id, "", "", "", "", "", "", None, [], today, tomorrow, yesterday, next_week
        )
        expected_creation = objects.Creation(
            id, today, tomorrow, ProvType.MergeRequestCreation
        )
        assert merge_request.creation == expected_creation

    def test_first_version(self):
        id = f"merge-request-id-{random_suffix()}"
        merge_request = objects.MergeRequest(
            id, "", "", "", "", "", "", None, [], today, tomorrow, yesterday, next_week
        )
        expected_version = objects.Version(id, ProvType.MergeRequestVersion)
        assert merge_request.first_version == expected_version

    def test_annotated_versions(self):
        id = f"merge-request-id-{random_suffix()}"
        aid1 = f"annotation-id-{random_suffix()}"
        aid2 = f"annotation-id-{random_suffix()}"
        annot1 = objects.Annotation(aid1, "", "", None, today, tomorrow)
        annot2 = objects.Annotation(aid2, "", "", None, today, tomorrow)
        annots = [annot1, annot2]
        merge_request = objects.MergeRequest(
            id,
            "",
            "",
            "",
            "",
            "",
            "",
            None,
            annots,
            today,
            tomorrow,
            yesterday,
            next_week,
        )
        ver1 = objects.AnnotatedVersion(
            id, annot1.id, ProvType.AnnotatedMergeRequestVersion
        )
        ver2 = objects.AnnotatedVersion(
            id, annot2.id, ProvType.AnnotatedMergeRequestVersion
        )
        expected_versions = [ver1, ver2]
        assert merge_request.annotated_versions == expected_versions


class TestTag:
    def test_identifier(self):
        name = f"tag-name-{random_suffix()}"
        hexsha = f"commit-sha-{random_suffix()}"
        msg = f"tag-message-{random_suffix()}"
        tag = objects.Tag(name, hexsha, msg, None, today)
        expected_identifier = qualified_name(
            f"Tag?{urlencode([('name', name), ('hexsha', hexsha)])}"
        )
        assert tag.prov_identifier == expected_identifier

    def test_attributes(self):
        name = f"tag-name-{random_suffix()}"
        hexsha = f"commit-sha-{random_suffix()}"
        msg = f"tag-message-{random_suffix()}"
        tag = objects.Tag(name, hexsha, msg, None, today)
        expected_attributes = [
            ("name", name),
            ("hexsha", hexsha),
            ("message", msg),
            ("created_at", today),
            (PROV_TYPE, ProvType.Tag),
            (PROV_TYPE, ProvType.Collection),
        ]
        assert tag.prov_attributes == expected_attributes

    def test_creation(self):
        name = f"tag-name-{random_suffix()}"
        tag = objects.Tag(name, "", "", None, today)
        expected_creation = objects.Creation(name, today, today, ProvType.TagCreation)
        assert tag.creation == expected_creation


class TestRelease:
    def test_identifier(self):
        name = f"release-name-{random_suffix()}"
        desc = f"release-description-{random_suffix()}"
        tag_name = f"tag-name-{random_suffix()}"
        release = objects.Release(name, desc, tag_name, None, [], [], today, tomorrow)
        expected_identifier = qualified_name(f"Release?{urlencode([('name', name)])}")
        assert release.prov_identifier == expected_identifier

    def test_attributes(self):
        name = f"release-name-{random_suffix()}"
        desc = f"release-description-{random_suffix()}"
        tag_name = f"tag-name-{random_suffix()}"
        release = objects.Release(name, desc, tag_name, None, [], [], today, tomorrow)
        expected_attributes = [
            ("name", name),
            ("description", desc),
            ("tag_name", tag_name),
            ("created_at", today),
            ("released_at", tomorrow),
            (PROV_TYPE, ProvType.Release),
            (PROV_TYPE, ProvType.Collection),
        ]
        assert release.prov_attributes == expected_attributes

    def test_creation(self):
        name = f"release-name-{random_suffix()}"
        release = objects.Release(name, "", "", None, [], [], today, tomorrow)
        expected_creation = objects.Creation(
            name, today, tomorrow, ProvType.ReleaseCreation
        )
        assert release.creation == expected_creation
