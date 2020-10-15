# Provenance Models

### Brew your own plots.
You can generate all figures that are displayed in the **Models** section by yourself and in a format of your desire.

Simply run the provided `model.py` script.

You will need to install the python package `prov` first. For a quick setup run:

```bash
pip install -r requirements.txt
```

# Models
## `git` Commit Model

#### Adding a file
This is the model for the addition of a new file to the project through a git commit.

The `Commit` activity represents the commit itself. The `Commit` activity is associated with two agents, the `Author` agent aswell as the `Committer` agent. These represent the users responsible  for authoring and committing the `git` commit.

The `Commit` activity generates two entities for the added file. One `File` entity representing the concept of the file itself and one `File Version` entity that represents the initial version of the added file. Both entities are attributed to the `Author` agent. The `Author` agent is assumed to not only having authored the commit but also the files contained in the commit. The `File Version` entity is related to to the `File` entity to mark it as a specialization of `File`.

The `Commit` activity is related to the activities representing the its parent commits. This only applies if the commit has any parents. The parent commits are represented by the `Parent Commit` activity in the model.

All following `File Version` entities will share the same original `File` entity and will always relate to their latest previous versions. This can be examined in the model for the modification of a file.

![Adding a file.](./svgs/git_commit_model_add.svg)
---


#### Modifying a file
This is the model for the modification of an already existing file by a `git` commit.

As usual a `Commit` activity represents the `git` commit itself. The modification of a file generates a new file version. This is represented by the `Commit` activity generating a new `File Version N` entity. The `commit activity` used the previous `File Version N-1` entity for the generation. The generated entity is related to the latest preceding `File Version N-1` entity and marked as being derived from it. The new `File Version N` entity is also related to the original `File` entity and marked as a specialization of it. The new `File Version` entity is attributed to the `Author` agent.

The `Commit` activity is associated with the `Author` agent and the `Committer` agent. They represent the users that are responsible for the authorship and commit respectivly.
The `Commit` activity is related to its parenting commit by a `wasInformedBy` relations.

Note: Due to the data retrieval approach of `gitlab2prov`, determining the latest preceding file version is not trivial. We deploy a workaround for this by creating a `File Version N-1` entity for each parenting commit and relating the generated `File Version` entity to those `File Version N-1` entities. In essence this still represents the file at its latest revision. Though as a result there can be more `File Version` entities than changes have been made to the file. This has to be considered when planning out queries.

![Modifying a file.](./svgs/git_commit_model_mod.svg)
---

#### Deleting a file
This is the model for the deletion of a file.

A `Commit` activity represents the `git` commit. The `Commit` activity is associated with the `Author` agent and the `Committer` agent representing the users that are responsible for the respective actions. The `Commit` activity is related to all of its parent commits.

We model the deletion of a file through a commit by spawning a special `File Version` entity which is imidiatly marked as invalidated by the `Commit` activity. This `File Version` entity is connected to the `File` entity by a `specializationOf` relationship. This allows to preserve the time at which the file got deleted.

![Deleting a file.](./svgs/git_commit_model_del.svg)
---

## The GitLab Web Resource Models

Most `git`-hosting platforms provide not only a `git` server but also platform specific features. For example, GitLab has an issue tracking system, allows discussions for each recorded `git` commit and provides the ability to post, discuss and review merge requests, etc. We model these features as event-driven resources. Events occur against resources and create new resource versions by doing so.

#### GitLab Commit Model

The models that we employ to capture user interactions on GitLab Web resources such as issues and merge requests do not differ significantly from one another.
Therefore we only explain one, as the underlying concept carries over to the remaining models.

The employed model can be partitioned into two sections.
The first section is concerned with the capture of the creation of a Web resource.
The second one models the evolution of such a resource over time as user and system initiated events occur against it.

Lets take the GitLab Commit Model as an example.
Immidiatly after GitLab receives a new `git` commit, GitLab creates a web interface for that commit.
The action of creating that interface is displayed by the `Commit Creation` activity.
The `Commit Creation` activity is related to the activity of the `git` commit that issued the Web resource creation.
The `Committer` of the `git` commit is marked as the `Creator` agent of the GitLab Commit Model that is responsible for the creation of the web resource.
Entities for the Commit Web resource (`Commit`) aswell as the initial version of that Web resource (`Commit Version`) are generated by the `Commit Creation` activity at the time of creation.

The second section is concerned with events that occur against the Web resource.
Such events are comments that users add to the resource aswell as other interactions such as reacting with emoji.
Each such event, that we call `Commit Annotations`, creates a new version of the web resource.
This version is represented by the `Annotated Commit Version` entity.
Each new resource version is marked as a specialization of the original web resource and as a derivation of the version preceding it.
This modeling approach can be compared to an event chain.

![GitLab Commit Model](./svgs/gitlab_commit_model.svg)

---

#### GitLab Issue Model

![GitLab Issue Model](./svgs/gitlab_issue_model.svg)

---

#### GitLab Merge Request Model

![GitLab Issue Model](./svgs/gitlab_merge_request_model.svg)

---

## Resource Events

GitLab displays events that can occur against resources on the pages of the respective resources. For example, if a resource was mentioned in the comment thread of another resource, this mention is displayed in the comment section of the mentioned target.

![comment thread](issue-thread.png)

These events can be parsed from multiple sources that are provided by the official GitLab API. Sadly there is no dedicated endpoint for all events that are of interest. Especially events that connect resources are difficult to get. Here a quick summary of what data needs to be retrieved, how to parse it and the workarounds that we deployed to achieve a prototypical event parsing.

For label events we use the official API endpoint from which we parse the appropriate events ("add_label", "remove_label").
Emoji awards can be retrieved from the appropriate API endpoint.
We parse everything else - such as mentions, time tracking stats, due dates, TODO's, etc. - from system notes that GitLab uses to display events in their web-interface. TODO: examine whether label events are included in system notes. The system notes are included in the comment thread for each resource and can be retrieved together with all regular notes from the note API endpoint.

System notes include a string that describe the event that they represent. We determine the event that the string denotes by regex based classifiers. If necessary we include named groups in the regular expressions to extract relevant information from the event strings. These are later added to PROV node labels.

Noted, this is not optimal as older GitLab versions employ different string notations for the same events. Sometimes only differing by a few characters and other times having a completly different string for the same event.
In addition there is a problem when looking at imported projects. For example, while looking at a project that was imported from SVN, relevant events wheren't recorded as system notes but rather as normal notes. This is not accounted for and is - as of right now - not covered by the current note parsing approach.

Here a list of events that we are currently able to parse with a short description of what the event is actually describing and the API resource from which we parse that event.

### List of Events

| Event Type                          | Description                                                                | Parsed API Resource |
|-------------------------------------|----------------------------------------------------------------------------|---------------------|
| `remove_label`                      | Removed label from a resource.                                             | Label Event         |
| `add_label`                         | Added label to a resource.                                                 | Label Event         |
| `award_emoji`                       | Awarded emoji to a resource or note.                                       | Award Emoji         |
| `comment`                           | Note added to the discussion thread of the resource.                       | Note                |
| `change_epic`                       | Exchanged epic that was attached to resource for another one.              | System Note         |
| `remove_from_external_epic`         | Remove resource from an epic that stems from another project.              | System Note         |
| `add_to_external_epic`              | Resource was added to an epic that belongs to another project.             | System Note         |
| `remove_from_epic`                  | Resource was removed from an epic of the same project.                     | System Note         |
| `add_to_epic`                       | Resource was added to an epic of the same project.                         | System Note         |
| `close_by_external_commit`          | Closeable Resource was closed by a commit from another project.            | System Note         |
| `close_by_external_merge_request`   | Closeable resource was closed by a merge request from another project.     | System Note         |
| `close_by_merge_request`            | Closeable resource was closed by a merge request from the same project.    | System Note         |
| `close_by_commit`                   | Closeable resource was closed by a commit from the same project.           | System Note         |
| `restore_source_branch`             | TODO: what is this event?                                                  | System Note         |
| `remove_label`                      | Removed label from a resource.                                             | System Note         |
| `add_label`                         | Added label to a resource.                                                 | System Note         |
| `create_branch`                     | Created branch for a merge request.                                        | System Note         |
| `mark_task_as_incomplete`           | Unchecked a checked (completed) task.                                      | System Note         |
| `mark_task_as_done`                 | Checked an uncompleted taks. This marks the task as done.                  | System Note         |
| `add_commits`                       | Added commits to a merge request.                                          | System Note         |
| `address_in_merge_request`          | Created a merge request from the commen thread of an issue.                | System Note         |
| `unmark_as_work_in_progress`        | Reset the WIP status of a resource. (issues, merge requests)               | System Note         |
| `mark_as_work_in_progress`          | Set the status of a resource to WIP. (issues, merge requests)              | System Note         |
| `merge`                             | Merged a merge request.                                                    | System Note         |
| `change_description`                | Changed the description of a resource. (issues, merge requests)            | System Note         |
| `change_title`                      | Changed the title of a resource. (issues, merge requests)                  | System Note         |
| `move_from`                         | Moved issue from another project to this project.                          | System Note         |
| `move_to`                           | Moved issue from this project to another project.                          | System Note         |
| `reopen`                            | Reopened a closeable resource.                                             | System Note         |
| `close`                             | Closed a closeable resource.                                               | System Note         |
| `unrelate_from_external_issue`      | Removed relation to an issue from another project.                         | System Note         |
| `relate_to_external_issue`          | Added relation to an issue from another project.                           | System Note         |
| `unrelate_from_issue`               | Removed relation to issue of the same project.                             | System Note         |
| `relate_to_issue`                   | Added relation to issue of the same project.                               | System Note         |
| `has_duplicate`                     | Mark another issue as a duplicate of this issue.                           | System Note         |
| `mark_as_duplicate`                 | Mark this issue as a duplicate of another issue.                           | System Note         |
| `make_visible`                      | Set the visibility status of the resource to unconfidential.               | System Note         |
| `make_confidential`                 | Set the visibility status of the resource to confidential.                 | System Note         |
| `remove_weight`                     | Removed the set weight of the resource.                                    | System Note         |
| `change_weight`                     | Changed the weight of a resource.                                          | System Note         |
| `remove_due_date`                   | Removed the due date of the resource.                                      | System Note         |
| `change_due_date`                   | Changed the due date of the resource.                                      | System Note         |
| `remove_time_estimate`              | Removed the time estimate value of the resource.                           | System Note         |
| `change_time_estimate`              | Changed the time estimate value of the resource.                           | System Note         |
| `unlock_merge_request`              | Unlocked the discussion thread of the merge request. (Enable comments)     | System Note         |
| `lock_merge_request`                | Locked the discussion thread of the merge request. (Disable comments)      | System Note         |
| `unlock_issue`                      | Unlocked the discussion thread of the issue. (Enable comments)             | System Note         |
| `lock_issue`                        | Locked the discussion thread of the issue. (Disable comments)              | System Note         |
| `remove_spend_time`                 | Removed time tracking stats from the resource.                             | System Note         |
| `subtract_spend_time`               | Subtracted an amount of time from the time tracking stats of the resource. | System Note         |
| `add_spend_time`                    | Added an amount of time to the time tracking stats of the resource.        | System Note         |
| `remove_milestone`                  | Removed milestone from the resource.                                       | System Note         |
| `change_milestone`                  | Changed milestone that was given to the resource to another milestone.     | System Note         |
| `unassign_user`                     | Unassigned a user from the assignable resource.                            | System Note         |
| `assign_user`                       | Assigned a user to the assignable resource.                                | System Note         |
| `mention_in_external_merge_request` | Mentioned the resource in a merge request from another project.            | System Note         |
| `mention_in_merge_request`          | Mentioned the resource in a merge request from the same project.           | System Note         |
| `mention_in_external_commit`        | Mentioned the resource in a commit from another project.                   | System Note         |
| `mention_in_commit`                 | Mentioned the resource in a commit from the same project.                  | System Note         |
| `mention_in_external_issue`         | Mentioned the resource in an issue from another project.                   | System Note         |
| `mention_in_issue`                  | Mentioned the resource in an issue from the same project.                  | System Note         |
