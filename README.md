Finds Github repositories that multiple people you are following have starred.
Creates a JSON feed that you can subscribe to and deploys it to Github Pages.

---

## Setup

In your Github Repository set up the following secrets:

- `FEED_AUTHOR`: A name for the "Author" field of the JSON Feed
- `FEED_NAME`: The filename for the JSON file that is generated (`.json` will be appended to this)
- `FEED_REPO`: The name of the repository (i.e. `multi-star`)
- `FEED_USERNAME`: The Github username of the user/organisation that owns the repository
- `GH_PAT`: A [Github token](https://github.com/settings/tokens) that has read access to the "followers" and "starring" categories

Update your repository settings to [allow Github actions read and write permissions to your repository](./settings/actions).

Once configured manually run the Github Action.

Finally, jump back into settings to enable Pages. It should deploy from the `gh-pages` branch.
