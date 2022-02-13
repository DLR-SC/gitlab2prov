import types
import enum

from prov.constants import PROV_ATTR_COLLECTION


class ChangeType(enum.Enum):
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNMERGED = "U"
    UNKNOWN = "X"
    BROKEN = "B"
    CHANGED = "T"


ProvRole = types.SimpleNamespace()
ProvRole.Committer = "Committer"
ProvRole.Author = "Author"
ProvRole.GitlabCommitAuthor = "GitlabCommitAuthor"
ProvRole.IssueAuthor = "IssueAuthor"
ProvRole.MergeRequestAuthor = "MergeRequestAuthor"
ProvRole.ReleaseAuthor = "ReleaseAuthor"
ProvRole.TagAuthor = "TagAuthor"
ProvRole.Annotator = "Annotator"
ProvRole.File = "File"
ProvRole.FileRevisionAtPointOfAddition = "FileRevisionAtPointOfAddition"
ProvRole.FileRevisionToBeModified = "FileRevisionToBeModified"
ProvRole.FileRevisionAfterModification = "FileRevisionAfterModification"
ProvRole.FileRevisionAtPointOfDeletion = "FileRevisionAtPointOfDeletion"
ProvRole.Resource = "Resource"
ProvRole.ResourceVersionAtPointOfCreation = "ResourceVersionAtPointOfCreation"
ProvRole.ResourceVersionToBeAnnotated = "ResourceVersionToBeAnnotated"
ProvRole.ResourceVersionAfterAnnotation = "ResourceVersionAfterAnnotation"
ProvRole.Release = "Release"
ProvRole.Tag = "Tag"
ProvRole.GitCommit = "GitCommit"


ProvType = types.SimpleNamespace()
ProvType.User = "User"
ProvType.GitCommit = "GitCommit"
ProvType.File = "File"
ProvType.FileRevision = "FileVersion"
ProvType.GitlabCommit = "GitlabCommit"
ProvType.GitlabCommitVersion = "GitlabCommitVersion"
ProvType.GitlabCommitCreation = "GitlabCommitCreation"
ProvType.AnnotatedGitlabCommitVersion = "AnnotatedGitlabCommitVersion"
ProvType.Issue = "Issue"
ProvType.IssueVersion = "IssueVersion"
ProvType.AnnotatedIssueVersion = "AnnotatedIssueVersion"
ProvType.IssueCreation = "IssueCreation"
ProvType.MergeRequest = "MergeRequest"
ProvType.MergeRequestVersion = "MergeRequestVersion"
ProvType.MergeRequestCreation = "MergeRequestCreation"
ProvType.AnnotatedMergeRequestVersion = "AnnotatedMergeRequestVersion"
ProvType.Annotation = "Annotation"
ProvType.Tag = "Tag"
ProvType.TagCreation = "TagCreation"
ProvType.Release = "Release"
ProvType.ReleaseCreation = "ReleaseCreation"
ProvType.Asset = "Asset"
ProvType.Evidence = "Evidence"
ProvType.Collection = PROV_ATTR_COLLECTION
