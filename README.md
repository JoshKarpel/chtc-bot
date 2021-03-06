# chtc-bot

## Events

Saying `gt#1000` will cause the CHTC bot to reply with a link to the corresponding GitTrac ticket.

Saying `rt#1001` will cause the CHTC bot to reply with a link to the corresponding RT ticket.

## Commands

`/knobs KNOB [KNOB_KNOB ...]`

The bot will look up the configuration knob(s) and echo them to the channel.

`/jobads ATTR [ATTR_ATTR ...]`

The bot will look up the job ad attribute(s) and echo them to the channel.

`/classad_eval 'AD' 'EXPR' ['EXPR' ...]`

The bot will simplify the given expression(s) in the context of the given ClassAd and echo the
ad (if not empty) and the result(s) to the channel.

`/submits COMMAND [COMMAND_COMMAND ...]`

The bot will look up the submit command(s) and echo them to the channel.

`/schedule [USER NAME, USER USER NAME, ...]`

On weekdays, the bot will send you a direct message with the day's schedule
status for the specified user(s), or all of them, if none are specified.  Use
the names displayed by the latter to discover the valid arguments to the
former.

`/condor_status [condor_status_args]`

Runs condor_status against (by default) the CHTC pool.  Use sparingly.

## Development

Once you've cloned the repository, run `pip install -r requirements-dev.txt`
to install the development packages.

This repository uses `pre-commit`.
After installing development dependencies, run `pre-commit install`.
**Do not commit before installing `pre-commit`!**

To run the tests, run `pytest` from the repository root.

## Deployment

CHTC-Bot is currently deployed on the CHTC Kubernetes cluster.

> There are also some files lying around from the now-deprecated Heroku deployment.

### Updating Version

Every commit to the repository generates a SHA-tagged Docker image via the
`.github/workflows/docker-build.yml` workflow.
The Docker Hub repository is
[here](https://hub.docker.com/repository/docker/chtcuw/chtc-bot).
To deploy a new version of the bot, follow the instructions in the configuration
repository to update the image version specified in the Kubernetes deployment
configuration.

### Expected Environment Variables

- `CONFIG` - The name of the configuration file in `config/` to load.
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `RSS_SHARED_SECRET`
- `SCHEDULE_COMMAND_PASSWORD`
- `DATABASE_URL` - Optional; database features will not be loaded if not present.

Some of these environment variables are secret, like the `SLACK_BOT_TOKEN`.
Use the "sealed secrets" described in the configuration repository to store
those secrets safely.
