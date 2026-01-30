# Copyright 2016-2017 LasLabs Inc.
# Copyright 2017-2018 Tecnativa - Jairo Llopis
# Copyright 2018-2019 Tecnativa - Alexandre Díaz
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Web Responsive",
    "summary": "Responsive web client, community-supported",
    "version": "14.0.1.2.2",
    "category": 'Themes/Backend',
    "website": "https://github.com/OCA/web",
    "author": " RND ",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["web", "mail"],
    "development_status": "Production/Stable",
    "maintainers": ["Yajo", "Tardo"],
    "data": ["views/assets.xml"],
    "qweb": [
        "static/src/xml/*.xml"
    ],
    "sequence": 1,
}
