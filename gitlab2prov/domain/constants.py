from prov.constants import PROV_ATTR_COLLECTION
from prov.model import PROV_ATTR_ENDTIME
from prov.model import PROV_ATTR_STARTTIME
from prov.model import PROV_LABEL
from prov.model import PROV_ROLE
from prov.model import PROV_TYPE


PROV_FIELD_MAP = {
    "prov_type": PROV_TYPE,
    "prov_role": PROV_ROLE,
    "prov_label": PROV_LABEL,
    "prov_start": PROV_ATTR_STARTTIME,
    "prov_end": PROV_ATTR_ENDTIME,
}


class ChangeType:
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNMERGED = "U"
    UNKNOWN = "X"
    BROKEN = "B"
    CHANGED = "T"


class ProvRole:
    GIT_COMMIT = "GitCommit"
    COMMIT = "Commit"
    COMMITTER = "Committer"
    AUTHOR = "Author"
    COMMIT_AUTHOR = "CommitAuthor"
    ISSUE_AUTHOR = "IssueAuthor"
    MERGE_REQUEST_AUTHOR = "MergeRequestAuthor"
    RELEASE_AUTHOR = "ReleaseAuthor"
    TAG_AUTHOR = "TagAuthor"
    ANNOTATOR = "Annotator"
    FILE = "File"
    FILE_REVISION_TO_BE_MODIFIED = "FileRevisionToBeModified"
    FILE_REVISION_AFTER_MODIFICATION = "FileRevisionAfterModification"
    FILE_REVISION_AT_POINT_OF_ADDITION = "FileRevisionAtPointOfAddition"
    FILE_REVISION_AT_POINT_OF_DELETION = "FileRevisionAtPointOfDeletion"
    RESOURCE = "Resource"
    FIRST_RESOURCE_VERSION = "FirstResourceVersion"
    RESOURCE_VERSION_AT_POINT_OF_CREATION = "ResourceVersionAtPointOfCreation"
    RESOURCE_VERSION_TO_BE_ANNOTATED = "ResourceVersionToBeAnnotated"
    RESOURCE_VERSION_AFTER_ANNOTATION = "ResourceVersionAfterAnnotation"
    PRE_ANNOTATION_VERSION = "PreAnnotationVersion"
    POST_ANNOTATION_VERSION = "PostAnnotationVersion"
    RELEASE = "Release"
    TAG = "Tag"
    GITCOMMIT = "GitCommit"
    ADDED_REVISION = "AddedRevision"
    DELETED_REVISION = "DeletedRevision"
    MODIFIED_REVISION = "ModifiedRevision"
    PREVIOUS_REVISION = "PreviousRevision"
    


class ProvType:
    USER = "User"
    GIT_COMMIT = "GitCommit"
    FILE = "File"
    FILE_REVISION = "FileRevision"
    COMMIT = "Commit"
    GITLAB_COMMIT_VERSION = "GitlabCommitVersion"
    GITLAB_COMMIT_VERSION_ANNOTATED = "AnnotatedGitlabCommitVersion"
    GITLAB_COMMIT_CREATION = "GitlabCommitCreation"
    GITHUB_COMMIT = "GithubCommit"
    GITHUB_COMMIT_VERSION = "GithubCommitVersion"
    GITHUB_COMMIT_VERSION_ANNOTATED = "AnnotatedGithubCommitVersion"
    GITHUB_COMMIT_CREATION = "GithubCommitCreation"
    ISSUE = "Issue"
    ISSUE_VERSION = "IssueVersion"
    ISSUE_VERSION_ANNOTATED = "AnnotatedIssueVersion"
    ISSUE_CREATION = "IssueCreation"
    MERGE_REQUEST = "MergeRequest"
    MERGE_REQUEST_VERSION = "MergeRequestVersion"
    MERGE_REQUEST_VERSION_ANNOTATED = "AnnotatedMergeRequestVersion"
    MERGE_REQUEST_CREATION = "MergeRequestCreation"
    PULL_REQUEST = "PullRequest"
    PULL_REQUEST_VERSION = "PullRequestVersion"
    PULL_REQUEST_VERSION_ANNOTAED = "AnnotatedPullRequestVersion"
    PULL_REQUEST_CREATION = "PullRequestCreation"
    CREATION = "Creation"
    ANNOTATION = "Annotation"
    TAG = "Tag"
    TAG_CREATION = "TagCreation"
    RELEASE = "Release"
    RELEASE_CREATION = "ReleaseCreation"
    ASSET = "Asset"
    EVIDENCE = "Evidence"
    COLLECTION = PROV_ATTR_COLLECTION
