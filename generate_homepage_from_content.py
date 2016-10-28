#!/usr/bin/env python

import argparse
import json
import os.path
import requests
import sys
import textwrap
import urllib
import yaml

from string import Template

# default filepaths
DEFAULT_CONTENT_YAML_PATH = './content.yml'
DEFAULT_PAGE_TEMPLATE_PATH = './index_template.html'
DEFAULT_OUTFILE_PATH = 'index.html'

# CSV keys and accepted values
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
WEBSITE_CONTENT_TEMPLATE = ('<span class="website-content">%s</span>\n'
                            '<span class="website-url">%s</span>')

# API endpoints and keys
TWITTER_OEMBED_ENDPOINT = 'https://publish.twitter.com/oembed?url=%s'
TWITTER_HTML_KEY = 'html'
INSTAGRAM_OEMBED_ENDPOINT = 'https://api.instagram.com/oembed/?url=%s'
INSTAGRAM_HTML_KEY = 'html'


def parse_command_line_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
        Generate an index.html file for www.notmylockerroom.com that formats
        the content provided (as yaml) into html (hitting the appropriate
        API to get embed code where necessary). The template html file should
        contain a '%s' where content should be inserted.

        Each row of the content represents a content element that will be
        put into the page.

        Type: one of 'twitter', 'instagram', or 'website'.
        Url: the url of the content (if twitter/instagram, a direct link to the
            tweet/photo)
        Quote: for 'website' only, the quote to highlight.
    """))
    parser.add_argument('--content', type=str,
                        help=('path to yaml file containing content (default: %s)' %
                              DEFAULT_CONTENT_YAML_PATH))
    parser.add_argument('--page_template', type=str,
                        help=('path to page template into which to insert '
                              'content (default: %s)' %
                              DEFAULT_PAGE_TEMPLATE_PATH))
    parser.add_argument('--outfile', type=str,
                        help=('path to write completed file to (default: %s)' %
                              DEFAULT_OUTFILE_PATH))
    return parser.parse_args()


def get_twitter_embed_code(url):
    """Given a URL, call twitter api for embed code."""
    # Twitter API expects url-encoded url
    encoded_url = urllib.quote(url)
    query_path = TWITTER_OEMBED_ENDPOINT % encoded_url
    response = requests.get(query_path)
    if response.status_code != 200:
        print ('Request to Twitter oEmbed endpoint for content "%s" failed '
               'with status code %d, message %s' %
               (url, response.status_code, response.content))

    else:
        result_json = json.loads(response.content)
        return result_json[TWITTER_HTML_KEY]


def get_instagram_embed_code(url):
    """Given a URL, call instagram api for embed code."""
    query_path = INSTAGRAM_OEMBED_ENDPOINT % url
    response = requests.get(query_path)
    if response.status_code != 200:
        print ('Request to Instagram oEmbed endpoint "%s" for content "%s" '
               'failed with status code %d, message "%s". Skipping.' %
               (query_path, url, response.status_code, response.content))
        return
    else:
        result_json = json.loads(response.content)
        return result_json[INSTAGRAM_HTML_KEY]


def html_element_from_embedded_content(url, content_type):
    """Given embeddable content (a source url for twitter or instagram), call
    the appropriate API to get embed code and insert into the appropriate HTML
    wrapper."""
    if content_type == CONTENT_TYPE_TWITTER:
        embed_code = get_twitter_embed_code(url)
    elif content_type == CONTENT_TYPE_INSTAGRAM:
        embed_code = get_instagram_embed_code(url)
    else:
        # We should have validated the content type before calling this func,
        # so this case should never get tripped.
        errString = ('Unexpected type %s (not an embedded content type). This '
                     'should never happen in this func.)' % content_type)
        raise ValueError(errString)
    return CONTENT_CONTAINER % (content_type, embed_code)


def html_element_from_website_content(url, quote):
    """Given website content (source url, quote), insert into the
    appropriate HTML template."""
    website_content = WEBSITE_CONTENT_TEMPLATE % (quote, url)
    return CONTENT_CONTAINER % ('website', website_content)


def html_element_from_content(content_dict):
    """Given a dict representing content (a type, a url, and optionally a
    quote), returns the content wrapped in the appropriate HTML element
    (ready for insertion on the homepage)."""
    content_type = content_dict.get(CSV_KEY_TYPE)
    if not content_type:
        print 'No content type provided for entry: "%s". Skipping.' % content_dict
        return
    elif content_type not in CONTENT_TYPES:
        print ('Unrecognized content type ("%s") in entry: "%s". Skipping.'
               % (content_type, content_dict))
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

    # make sure to escape any lone '%' signs
    return elem.replace('%', '%%')


def content_from_yaml(filepath):
    """Given the filepath of a yaml file containing content, returns a dict of
    content information."""
    with open(filepath) as stream:
      try:
        contents = yaml.load(stream)
      except yaml.YAMLError as ex:
        print ex
    return contents

def validate_filepath(filepath):
    """Make sure given filepath is a valid file."""
    if not os.path.isfile(filepath):
        print ('ERROR: Filepath provided ("%s") is not a file (may be a '
               'directory or an invalid path).' % filepath)
        sys.exit(1)
    return


def main():
    args = parse_command_line_args()

    # set filepaths from command line args or default, validate filepaths.
    if args.content:
        content_yaml_filepath = args.content
    else:
        print 'No content yaml filepath provided, using default: %s' % DEFAULT_CONTENT_YAML_PATH
        content_yaml_filepath = DEFAULT_CONTENT_YAML_PATH
    validate_filepath(content_yaml_filepath)

    if args.page_template:
        page_template_filepath = args.page_template
    else:
        print 'No page template filepath provided, using default: %s' % DEFAULT_PAGE_TEMPLATE_PATH
        page_template_filepath = DEFAULT_PAGE_TEMPLATE_PATH
    validate_filepath(page_template_filepath)

    if args.outfile:
        outfile_filepath = args.outfile
    else:
        print 'No outfile filepath provided, using default: %s' % DEFAULT_OUTFILE_PATH
        outfile_filepath = DEFAULT_OUTFILE_PATH

    print '-'*80

    # read in content yaml, generate html elements for each piece of content
    # (getting embed code from API where appropriate.)
    content = content_from_yaml(content_yaml_filepath)
    print 'Loaded %d social media rows from yaml.' % len(content['social'])
    html_elements_to_add = []
    for s in content['social']:
      elem = html_element_from_content(s)
      html_elements_to_add.append(elem)

    # insert generated content into page template
    with open(page_template_filepath) as infile:
        page_template = infile.read()

    formatted = '\n\n'.join(html_elements_to_add)

    content['formattedsocial'] = formatted

    generated_page = Template(page_template).substitute(content)

    # write results to file
    with open(outfile_filepath, 'w') as outfile:
        outfile.write(generated_page)

    print 'Succesfully wrote generated page to %s' % outfile_filepath


if __name__ == '__main__':
    main()
