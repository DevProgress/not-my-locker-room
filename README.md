# not-my-locker-room

### How to use the code in this repo

First make sure you have all the necessary modules: `pip install -r requirements.txt`

Add a yaml file with data for title, tagline, photocredit, heading, and a list of
social media links (see `content.yml` or `dummy_content.yml` for examples). Then run
`generate_homepage_from_content.py` to build the page. For example:

```
./generate_homepage_from_content.py --content content.yml --outfile not_my_locker_room.html
```

or

```
./generate_homepage_from_content.py --content endorsements.yml --outfile
endorsements.html
```

You can always run `./generate_homepage_from_content.py -h` for help & usage instructions.

### How to add a new type of social content
Say you want to embed some content from hip social media platform Latergram, which has an API endpoint that takes a content URL and returns you embed HTML code for that content.

**Step 1**: add a constant for your new content type in the `# keys and accepted values` section:
```
CONTENT_TYPE_LATERGRAM = 'latergram'
```
We can now match any social media row in the `content.yml` file of `type: latergram` to the appropriate API info.

**Step 2**: add a key/value pair in the `API_INFOS` dict.:
```
API_INFOS = {
    ...
    CONTENT_TYPE_LATERGRAM:  {
                                'endpoint': 'https://api.latergram.com/oembed/?url=%s',
                                'response_html_key': 'html',
                                'encode_url': False
                             },
    ...
}
```
The key should be the constant for your content type defined in step 1. The value is a dict. with the following pieces of information:
* `endpoint`: Latergram's API endpoint for getting embed HTML code, prepared for string formatting (i.e. put `%s` wherever the URL to the content you're trying to embed should go). Presumes the endpoint requires no other params. besides a content URL.
* `response_html_key`:  assuming a JSON blob as a response from the endpoint, this is the key where the embed HTML is stored (for instance, look at a [Twitter oEmbed example response](https://dev.twitter.com/rest/reference/get/statuses/oembed#example-response); the `response_html_key` in this case would be `html`.)
* `encode_url`: set to `True` if the API endpoint expects a URL-encoded content URL, otherwise set to `False`.