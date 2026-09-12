{
    "name": "Financa Consultores Website",
    "version": "19.0.1.0.0",
    "category": "Website/Website",
    "summary": "Homepage corporativa de Financa Consultores",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "data/redirects.xml",
        "views/homepage.xml",
        "views/snippets.xml",
        "views/legal.xml",
        "views/thank_you.xml",
        "data/homepage_ensure.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "financa_website/static/src/scss/financa.scss",
            "financa_website/static/src/js/financa_animations.js",
            "financa_website/static/src/js/financa_tracking.js",
            "financa_website/static/src/js/financa_experiments.js",
        ],
    },
    "installable": True,
    "application": False,
}

