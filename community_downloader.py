#!/usr/bin/env python
# Modified from original at: https://github.com/egbertbouman/youtube-comment-downloader

from __future__ import print_function

import argparse
import io
import json
import os
import sys
import time

import re
import requests

YOUTUBE_VIDEO_URL = 'https://www.youtube.com/post/{youtube_id}'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

SORT_BY_POPULAR = 0
SORT_BY_RECENT = 1

YT_CFG_RE = r'ytcfg\.set\s*\(\s*({.+?})\s*\)\s*;'
YT_INITIAL_DATA_RE = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;\s*(?:var\s+meta|</script|\n)'


def regex_search(text, pattern, group=1, default=None):
    match = re.search(pattern, text)
    return match.group(group) if match else default


def ajax_request(session, endpoint, ytcfg, retries=5, sleep=20):
    url = 'https://www.youtube.com' + endpoint['commandMetadata']['webCommandMetadata']['apiUrl']
    
    data = {'context': ytcfg['INNERTUBE_CONTEXT'],
            'continuation': endpoint['continuationCommand']['token']}

    for _ in range(retries):
        response = session.post(url, params={'key': ytcfg['INNERTUBE_API_KEY']}, json=data)
        if response.status_code == 200:
            return response.json()
        if response.status_code in [403, 413]:
            return {}
        else:
            time.sleep(sleep)

# Partial code taken from download_comments, just to get the URL or other info about post
def get_post_channel_url(youtube_id):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))
    if 'uxe=' in response.request.url:
        session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
        response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))
    html = response.text
    ytcfg = json.loads(regex_search(html, YT_CFG_RE, default=''))
    if not ytcfg:
        return None # Unable to extract configuration
    data = json.loads(regex_search(html, YT_INITIAL_DATA_RE, default=''))
    try:
        channelURL = data['microformat']['microformatDataRenderer']['urlCanonical']
        return channelURL
    except KeyError:
        return None

def download_comments(youtube_id, sort_by=SORT_BY_RECENT, language=None, sleep=.1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))

    if 'uxe=' in response.request.url:
        session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
        response = session.get(YOUTUBE_VIDEO_URL.format(youtube_id=youtube_id))

    html = response.text
    ytcfg = json.loads(regex_search(html, YT_CFG_RE, default=''))
    if not ytcfg:
        return # Unable to extract configuration
    if language:
        ytcfg['INNERTUBE_CONTEXT']['client']['hl'] = language

    data = json.loads(regex_search(html, YT_INITIAL_DATA_RE, default=''))

    section = next(search_dict(data, 'itemSectionRenderer'), None)
    renderer = next(search_dict(section, 'continuationItemRenderer'), None) if section else None
    if not renderer:
        # Comments disabled?
        return

    needs_sorting = sort_by != SORT_BY_POPULAR
    continuations = [renderer['continuationEndpoint']]
    while continuations:
        continuation = continuations.pop()
        response = ajax_request(session, continuation, ytcfg)

        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' + next(search_dict(response, 'externalErrorMessage')))

        if needs_sorting:
            sort_menu = next(search_dict(response, 'sortFilterSubMenuRenderer'), {}).get('subMenuItems', [])
            if sort_by < len(sort_menu):
                continuations = [sort_menu[sort_by]['serviceEndpoint']]
                needs_sorting = False
                continue
            raise RuntimeError('Failed to set sorting')

        actions = list(search_dict(response, 'reloadContinuationItemsCommand')) + \
                  list(search_dict(response, 'appendContinuationItemsAction'))
        for action in actions:
            for item in action.get('continuationItems', []):
                if action['targetId'] == 'comments-section':
                    # Process continuations for comments and replies.
                    continuations[:0] = [ep for ep in search_dict(item, 'continuationEndpoint')]
                if action['targetId'].startswith('comment-replies-item') and 'continuationItemRenderer' in item:
                    # Process the 'Show more replies' button
                    continuations.append(next(search_dict(item, 'buttonRenderer'))['command'])

        for comment in reversed(list(search_dict(response, 'commentRenderer'))):
            yield {'cid': comment['commentId'],
                   'text': ''.join([c['text'] for c in comment['contentText'].get('runs', [])]),
                   'time': comment['publishedTimeText']['runs'][0]['text'],
                   'author': comment.get('authorText', {}).get('simpleText', ''),
                   'channel': comment['authorEndpoint']['browseEndpoint'].get('browseId', ''),
                   'votes': comment.get('voteCount', {}).get('simpleText', '0'),
                   'photo': comment['authorThumbnail']['thumbnails'][-1]['url'],
                   'heart': next(search_dict(comment, 'isHearted'), False)}

        time.sleep(sleep)


def search_dict(partial, search_key):
    stack = [partial]
    while stack:
        current_item = stack.pop()
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                if key == search_key:
                    yield value
                else:
                    stack.append(value)
        elif isinstance(current_item, list):
            for value in current_item:
                stack.append(value)


def main(communityPostID=None, limit=1000, sort=SORT_BY_RECENT, language=None):
    try:
        if not communityPostID:
            raise ValueError('you need to specify a Youtube ID')

        print('Loading Youtube comments for post:', communityPostID)
        count = 0
        sys.stdout.write('Loaded %d comment(s)\r' % count)
        sys.stdout.flush()
        start_time = time.time()

        commentsDict = {}
        for comment in download_comments(communityPostID, sort, language):
            commentID = comment['cid']
            commentText = comment['text']
            authorName = comment['author']
            authorChannelID = comment['channel']
            commentsDict[commentID] = {'commentText': commentText, 'authorName':authorName, 'authorChannelID':authorChannelID}

            #comment_json = json.dumps(comment, ensure_ascii=False)
            count += 1
            sys.stdout.write('Downloaded %d comment(s)\r' % count)
            sys.stdout.flush()
            if limit and count >= limit:
                break
        print('\n[{:.2f} seconds] Done!'.format(time.time() - start_time))

        return commentsDict

    except Exception as e:
        print('Error:', str(e))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
