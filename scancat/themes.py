"""Probe a WordPress site for theme information."""
import logging

import requests
from bs4 import BeautifulSoup

from . import wordpress as wp
from .message import msg


def is_genesis_child_theme(soup=None):
    """Is the active theme a Genesis child theme?

    :param soup: The parsed HTML, defaults to None
    :param soup: BeautifulSoup, optional
    :return: True if Genesis child theme detected
    :rtype: bool
    """
    if soup is None:
        logging.info('⚠️ No HTML content available.')
        return
    info, _ = theme_info(soup)
    if info is None:
        msg.send('ℹ️ A Genesis child theme was not found (or may be minified).')
        return False
    if 'template' in info and info['template'].lower() == 'genesis':
        msg.send('🎨 A Genesis child theme is active.')
        return True


def print_genesis_info(soup=None):
    """Get Genesis parent theme version info if it can be found.

    :param soup: The parsed HTML, defaults to None
    :param soup: BeautifulSoup, optional
    """
    if soup is None:
        logging.info('⚠️ No HTML content available.')
        return
    _, child_theme_style_url = theme_info(soup)
    if child_theme_style_url:
        genesis_style_url = child_theme_style_url.split(
            '/wp-content/', 1)[0] + '/wp-content/themes/genesis/style.css'
        genesis_theme_info, url = theme_info(None, [genesis_style_url])
        if genesis_theme_info and url:
            msg.send('• Genesis version: ' +
                     genesis_theme_info['version'] + ' <a href="{0}" target="_blank">{0}</a>'.format(url))


def stylesheets(soup=None):
    """Find stylesheet URLs in HTML code.

    :param soup: The parsed HTML, defaults to None
    :param soup: BeautifulSoup, optional
    :return: All stylesheet URLs from link tags
    :rtype: list
    """
    if soup is None:
        logging.info('⚠️ No HTML content available.')
        return
    links = soup.findAll('link', attrs={'rel': 'stylesheet'})
    stylesheet_urls = [link["href"] for link in links]
    return stylesheet_urls


def theme_info(soup=None, theme_stylesheet_urls=None):
    """Get active theme information.

    :param soup: The parsed HTML, defaults to None
    :param soup: BeautifulSoup, optional
    :param theme_stylesheet_urls: List of stylesheet URLs, defaults to None
    :param theme_stylesheet_urls: list, optional
    :return: Tuple of theme info and the stylesheet URL
    :rtype: list, string or None, None
    """
    if soup is None and theme_stylesheet_urls is None:
        logging.info('⚠️ No HTML content available.')
        return None, None
    if theme_stylesheet_urls is None:
        stylesheet_urls = stylesheets(soup)
        theme_stylesheet_urls = list(
            filter(lambda url: '/themes/' in url, stylesheet_urls))
    for url in theme_stylesheet_urls:
        css = requests.get(url)
        info = wp.parse_stylesheet_header(css.text)
        if 'theme_name' in info:
            return info, url
    return None, None


def print_theme_info(soup=None):
    """Print active theme information.

    :param soup: The parsed HTML, defaults to None
    :param soup: BeautifulSoup, optional
    """
    not_found_message = 'No theme info found. Styles may be minified, in an unexpected place, behind a maintenance mode page, or the site is not using WordPress.'
    if soup is None:
        logging.info('⚠️ No HTML content available.')
        return
    info, url = theme_info(soup)
    if info is None:
        msg.send(not_found_message)
        return
    if 'theme_name' in info:
        msg.send('• Theme name: ' + info['theme_name'])
    else:
        msg.send(not_found_message)
    if 'version' in info:
        msg.send('• Version: ' + info['version'] +
                 ' <a href="{0}" target="_blank">{0}</a>'.format(url))
