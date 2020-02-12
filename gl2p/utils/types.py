"""
Type definitions for static type checking. (MyPy)

As of yet, the typing resolution does not cover
the type of dictionary keys.
"""

from typing import Dict, Any, List


# A commit resource as returned by the GitLab
# API is a dictionary mapping from keys to values.
#
# An example can be found here:
#   https://docs.gitlab.com/ee/api/commits.html#get-a-single-commit
#
# Different API versions provide a different set
# of keys. For example GitLab Bronze, Silver and
# Gold allow for issue weights. The free version
# does not cover these.
Commit = Dict[str, Any]


# An issue resource as returned by the GitLab API
# is a dictionary mapping from keys to values.
#
# An example can be found here:
#   https://docs.gitlab.com/ee/api/issues.html#single-issue
Issue = Dict[str, Any]


# A merge request resource as returned by the GitLab API
# is a dictionary mapping from keys to values.
#
# An example can be found here:
#   https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr
MergeRequest = Dict[str, Any]


# A diff, as returned by the GitLab API, is
# represented by a list of entries which in turn
# are dictionary mappings.
#
# An example can be found here:
#   https://docs.gitlab.com/ee/api/commits.html#get-the-diff-of-a-commit
Diff = List[Dict[str, Any]]


# A note as returned by the GitLab API is a
# dictionary mapping. There is no difference between
# issue notes, merge request notes and commit notes.
#
# An example can be found here:
#   https://docs.gitlab.com/ee/api/notes.html#notes-pagination
#
# The way to obtain commit notes differs from the way
# that one obtains issue or merge request notes.
# Notes can be retrieved as organized discussion threads.
# Every note that is not a reply is it's own thread.
# Replies to a note are recorded in the thread of
# the top level note. In contrast to issue and
# merge request notes there is no API endpoint to
# simply list all notes of a commit. One can get
# these by requesting all discussions of a commit
# and extracting the notes from the "note" key of
# every discussion.
Note = Dict[str, Any]


# A label event as returned by the GitLab API is a
# dictionary mapping from keys to values.
#
# An example can be found here:
#  https://docs.gitlab.com/ee/api/resource_label_events.html#list-project-issue-label-events
Label = Dict[str, Any]

# An award emoji as returned by the GitLab API is a
# dictionary mapping from keys to values.
#
# An example can be found here:
#   https://docs.gitlab.com/ee/api/award_emoji.html#get-single-award-emoji
Award = Dict[str, Any]
