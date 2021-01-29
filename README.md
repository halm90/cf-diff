# cf-diff
*cf-fetcher* difference tool (see JIRA CF-576).

*cf-fetcher* is an application that syncs an external sql database with a
subset of the current state of the *Cloud Controller*, however the database
may not be perfectly in sync with the actual *Cloud Controller*.  The intent
of this tool is to periodically query the *Cloud Controller* to get a reliable
list (and count) of application instances, and compare that to the list in the
*cf-fetcher* maintained database.

Currently this tool (and CF-576) are concerned only with exposing the diff information,
and not acting on the information. 

## Reference(s):
1. Tables/resources to diff are found here: https://iasgit.internal.t-mobile.com/ias-cf/cf-fetcher/tree/master/actor/dbaction

## Getting started
### Required Environment Variables
The following environment variables are required:
  1. *OAUTH_CLIENT_ID*: client id used to authenticate (for CloudController)
  2. *OAUTH_CLIENT_SECRET*: client 'secret' used to authenticate (for CloudController)
  4. *FOUNDATION*: Foundation to query (ie: *px-stg*)
  5. *CC_URL*: URL of the CloudController


### Notes:
  1. *OAUTH_URL* is no longer required as the URL is fetched directly from the CloudController.
