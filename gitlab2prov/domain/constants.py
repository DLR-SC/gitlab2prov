import prov.model
import prov.constants


PROV_FIELD_MAP = {
    "prov_type": prov.model.PROV_TYPE,
    "prov_role": prov.model.PROV_ROLE,
    "prov_label": prov.model.PROV_LABEL,
    "prov_start": prov.model.PROV_ATTR_STARTTIME,
    "prov_end": prov.model.PROV_ATTR_ENDTIME,
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
    COMMITTER = "Committer"
    AUTHOR = "Author"
    AUTHOR_GITLAB_COMMIT = "GitlabCommitAuthor"
    AUTHOR_ISSUE = "IssueAuthor"
    AUTHOR_MERGE_REQUEST = "MergeRequestAuthor"
    AUTHOR_RELEASE = "ReleaseAuthor"
    AUTHOR_TAG = "TagAuthor"
    ANNOTATOR = "Annotator"
    FILE = "File"
    FILE_REVISION_TO_BE_MODIFIED = "FileRevisionToBeModified"
    FILE_REVISION_AFTER_MODIFICATION = "FileRevisionAfterModification"
    FILE_REVISION_AT_POINT_OF_ADDITION = "FileRevisionAtPointOfAddition"
    FILE_REVISION_AT_POINT_OF_DELETION = "FileRevisionAtPointOfDeletion"
    RESOURCE = "Resource"
    RESOURCE_VERSION_AT_POINT_OF_CREATION = "ResourceVersionAtPointOfCreation"
    RESOURCE_VERSION_TO_BE_ANNOTATED = "ResourceVersionToBeAnnotated"
    RESOURCE_VERSION_AFTER_ANNOTATION = "ResourceVersionAfterAnnotation"
    RELEASE = "Release"
    TAG = "Tag"
    GitCommit = "GitCommit"


class ProvType:
    USER = "User"
    GIT_COMMIT = "GitCommit"
    FILE = "File"
    FILE_REVISION = "FileRevision"
    GITLAB_COMMIT = "GitlabCommit"
    GITLAB_COMMIT_VERSION = "GitlabCommitVersion"
    GITLAB_COMMIT_VERSION_ANNOTATED = "AnnotatedGitlabCommitVersion"
    GITLAB_COMMIT_CREATION = "GitlabCommitCreation"
    ISSUE = "Issue"
    ISSUE_VERSION = "IssueVersion"
    ISSUE_VERSION_ANNOTATED = "AnnotatedIssueVersion"
    ISSUE_CREATION = "IssueCreation"
    MERGE_REQUEST = "MergeRequest"
    MERGE_REQUEST_VERSION = "MergeRequestVersion"
    MERGE_REQUEST_VERSION_ANNOTATED = "AnnotatedMergeRequestVersion"
    MERGE_REQUEST_CREATION = "MergeRequestCreation"
    ANNOTATION = "Annotation"
    TAG = "Tag"
    TAG_CREATION = "TagCreation"
    RELEASE = "Release"
    RELEASE_CREATION = "ReleaseCreation"
    ASSET = "Asset"
    EVIDENCE = "Evidence"
    COLLECTION = prov.constants.PROV_ATTR_COLLECTION
