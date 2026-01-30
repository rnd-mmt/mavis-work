# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import logging
from odoo.loglevels import ustr
from lxml import etree
from odoo.tools.mail import _Cleaner
from odoo.tools import pycompat, misc

tags_to_kill = [
    "script",
    "head",
    "meta",
    "title",
    "link",
    "frame",
    "base",
]

tags_to_remove = [
    'html',
    'body',
]


def html_sanitize(
    src,
    silent=True,
):
    if not src:
        return src

    src = ustr(src, errors='replace')

    # html: remove encoding attribute inside tags
    doctype = re.compile(r'(<[^>]*\s)(encoding=(["\'][^"\']*?["\']|[^\s\n\r>]+)(\s[^>]*|/)?>)', re.IGNORECASE | re.DOTALL)
    src = doctype.sub(u"", src)

    logger = logging.getLogger(__name__ + '.html_sanitize')

    # html encode email tags
    part = re.compile(r"(<(([^a<>]|a[^<>\s])[^<>]*)@[^<>]+>)", re.IGNORECASE | re.DOTALL)
    # remove results containing cite="mid:email_like@address" (ex: blockquote cite)
    # cite_except = re.compile(r"^((?!cite[\s]*=['\"]).)*$", re.IGNORECASE)
    src = part.sub(lambda m: (u'cite=' not in m.group(1) and u'alt=' not in m.group(1)) and misc.html_escape(m.group(1)) or m.group(1), src)
    # html encode mako tags <% ... %> to decode them later and keep them alive, otherwise they are stripped by the cleaner
    src = src.replace(u'<%', misc.html_escape(u'<%'))
    src = src.replace(u'%>', misc.html_escape(u'%>'))

    kwargs = {
        'page_structure': True,
        'style': False,
        'forms': False,
        'embedded': False,
        'remove_unknown_tags': False,
        'comments': False,
        'processing_instructions': False,
        'kill_tags': tags_to_kill,
        'remove_tags': tags_to_remove,
        'safe_attrs_only': False,
    }

    try:
        # some corner cases make the parser crash (such as <SCRIPT/XSS SRC=\"http://ha.ckers.org/xss.js\"></SCRIPT> in test_mail)
        cleaner = _Cleaner(**kwargs)
        cleaned = cleaner.clean_html(src)
        assert isinstance(cleaned, pycompat.text_type)
        # MAKO compatibility: $, { and } inside quotes are escaped, preventing correct mako execution
        cleaned = cleaned.replace(u'%24', u'$')
        cleaned = cleaned.replace(u'%7B', u'{')
        cleaned = cleaned.replace(u'%7D', u'}')
        cleaned = cleaned.replace(u'%20', u' ')
        cleaned = cleaned.replace(u'%5B', u'[')
        cleaned = cleaned.replace(u'%5D', u']')
        cleaned = cleaned.replace(u'%7C', u'|')
        cleaned = cleaned.replace(u'&lt;%', u'<%')
        cleaned = cleaned.replace(u'%&gt;', u'%>')
        # html considerations so real html content match database value
        cleaned.replace(u'\xa0', u'&nbsp;')
    except etree.ParserError as e:
        if u'empty' in pycompat.text_type(e):
            return u""
        if not silent:
            raise
        logger.warning(u'ParserError obtained when sanitizing %r', src, exc_info=True)
        cleaned = u'<p>ParserError when sanitizing</p>'
    except Exception:
        if not silent:
            raise
        logger.warning(u'unknown error obtained when sanitizing %r', src, exc_info=True)
        cleaned = u'<p>Unknown error when sanitizing</p>'

    # this is ugly, but lxml/etree tostring want to put everything in a 'div' that breaks the editor -> remove that
    if cleaned.startswith(u'<div>') and cleaned.endswith(u'</div>'):
        cleaned = cleaned[5:-6]

    return cleaned
