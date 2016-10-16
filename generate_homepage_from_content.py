#!/usr/bin/env python

import csv
import json
import os.path
import requests
import sys
import urllib

# TODO: string formatting by dict/key to be cleaner
DEFAULT_CONTENT_CSV_PATH = './content.csv'
DEFAULT_PAGE_TEMPLATE_PATH = './index_template.html'
DEFAULT_OUTFILE_PATH = 'index.html'

CSV_KEY_TYPE = 'type'
CSV_KEY_URL = 'url'
CSV_KEY_QUOTE = 'quote'
CONTENT_TYPE_TWITTER = 'twitter'
CONTENT_TYPE_INSTAGRAM = 'instagram'
CONTENT_TYPE_WEBSITE = 'website'
CONTENT_TYPES = [CONTENT_TYPE_TWITTER, CONTENT_TYPE_INSTAGRAM, CONTENT_TYPE_WEBSITE]
EMBEDDED_CONTENT_TYPES = [CONTENT_TYPE_TWITTER, CONTENT_TYPE_INSTAGRAM]

# HTML templates
CONTENT_CONTAINER = '<div class="content %s">%s</div>'
WEBSITE_CONTENT_TEMPLATE = '<span class="website-content">%s</span>\n<span class="website-url">%s</span>'

# API endpoints and keys
TWITTER_OEMBED_ENDPOINT = 'https://publish.twitter.com/oembed?url=%s' # url-encoded
TWITTER_HTML_KEY = 'html'
INSTAGRAM_OEMBED_ENDPOINT = 'https://api.instagram.com/oembed/?url=%s'
INSTAGRAM_HTML_KEY = 'html'


def get_twitter_embed_code(url):
    encoded_url = urllib.quote(url)
    query_path = TWITTER_OEMBED_ENDPOINT % encoded_url
    response = requests.get(query_path)
    if response.status_code != 200:
        print 'Request to Twitter oEmbed endpoint for content "%s" failed with status code %d, message %s' % (url, response.status_code, response.content)
    else:
        result_json = json.loads(response.content)
        return result_json[TWITTER_HTML_KEY]


def get_instagram_embed_code(url):
    query_path = INSTAGRAM_OEMBED_ENDPOINT % url
    response = requests.get(query_path)
    if response.status_code != 200:
        # *** wrap this, say 'skipping', give url i tried to hit, format better
        print 'Request to Instagram oEmbed endpoint for content "%s" failed with status code %d, message %s.' % (url, response.status_code, response.content)
        return
    else:
        result_json = json.loads(response.content)
        return result_json[INSTAGRAM_HTML_KEY]


def html_element_from_embedded_content(url, content_type):
    # uhhhh i should do this checking in html_elem_from_content so it's all in one place
    if content_type == CONTENT_TYPE_TWITTER:
        embed_code = get_twitter_embed_code(url)
    elif content_type == CONTENT_TYPE_INSTAGRAM:
        embed_code = get_instagram_embed_code(url)
    else:
        # We should have validated the content type before calling this func, so
        # this case should never get tripped.
        errString = 'Unexpected type %s (not an embedded content type). This should never happen.' % content_type
        raise ValueError(errString)
    return CONTENT_CONTAINER % (content_type, embed_code)


def html_element_from_website_content(url, quote):
    website_content = WEBSITE_CONTENT_TEMPLATE % (quote, url)
    return CONTENT_CONTAINER % ('website', website_content)


"""Given a dict representing content (a type, a url, and optionally a quote),
   returns the content wrapped in the appropriate HTML element (ready for
   insertion on the homepage)."""
def html_element_from_content(content_dict):
    content_type = content_dict.get(CSV_KEY_TYPE)
    if not content_type:
        print 'No content type provided for entry: "%s". Skipping.' % content_dict
        return
    elif content_type not in CONTENT_TYPES:
        print 'Unrecognized content type ("%s") in entry: "%s". Skipping.' % (content_type, content_dict)
        return
    elif content_type in EMBEDDED_CONTENT_TYPES:
        url = content_dict.get(CSV_KEY_URL)
        if not url:
            print 'No url provided for entry: "%s". Skipping.' % content_dict
            return
        elem = html_element_from_embedded_content(url, content_type)
    elif content_type == CONTENT_TYPE_WEBSITE:
        url = content_dict.get(CSV_KEY_URL)
        quote = content_dict.get(CSV_KEY_QUOTE)
        elem = html_element_from_website_content(url, quote)

    return elem


"""Given the filepath of a csv containing content, returns a generator that
   yields each row as a dict."""
def content_from_csv(filepath):
    return csv.DictReader(open(filepath))

def validate_filepath(filepath):
    if not os.path.isfile(filepath):
        print ('ERROR: Filepath provided ("%s") is not a file (may be a '
               'directory or an invalid path).' % filepath)
        sys.exit(1)
    return

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        Generate an index.html file for www.notmylockerroom.com that formats the content provided (as a csv) into stuff.
    """))
    parser.add_argument('--content_csv', type=str,
                        help='path to csv containing content (default: ./content.csv)')
    parser.add_argument('--page_template', type=str,
                        help='path to page template into which to insert content (default: ./index_template.html)')
    parser.add_argument('--outfile', type=str,
                        help='path to write completed file to (default: ./index.html)')
    args = parser.parse_args()


    if args.content_csv:
        content_csv_filepath = args.content_csv
    else:
        print 'No content csv filepath provided, using default: %s' % DEFAULT_CONTENT_CSV_PATH
        content_csv_filepath = DEFAULT_CONTENT_CSV_PATH
    validate_filepath(content_csv_filepath)

    if args.page_template:
        page_template_filepath = args.page_template
    else:
        print 'No page template filepath provided, using default: %s' % DEFAULT_PAGE_TEMPLATE_PATH
        page_template_filepath = DEFAULT_PAGE_TEMPLATE_PATH
    validate_filepath(page_template_filepath)

    if args.outfile:
        page_template_filepath = args.outfile
    else:
        print 'No outfile filepath provided, using default: %s' % DEFAULT_OUTFILE_PATH
        outfile_filepath = DEFAULT_OUTFILE_PATH

    content = content_from_csv(content_csv_filepath)
    html_elements_to_add = []
    for row in content:
        elem = html_element_from_content(row)
        html_elements_to_add.append(elem)

    # gonna hardcode the other filepaths (to the rest of the template) for now
    with open(page_template_filepath) as infile:
        page_template = infile.read()

    generated_page = page_template % '\n\n'.join(html_elements_to_add)

    with open(outfile_filepath, 'w') as outfile:
        outfile.write(generated_page)


if __name__ == '__main__':
    main()
