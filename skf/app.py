# -*- coding: utf-8 -*-
"""
    Security Knowledge Framework is an expert system application
    that uses OWASP Application Security Verification Standard, code examples
    and helps developers in pre-development & post-development.
    Copyright (C) 2017 Glenn ten Cate, Riccardo ten Cate
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.
    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import logging.config, click, os, re

from flask import Flask, Blueprint
from sqlite3 import dbapi2 as sqlite3
from sqlalchemy import text
from flask_bcrypt import Bcrypt
from skf import settings
from skf.api.user.endpoints.activate import ns as users_activate_namespace
from skf.api.kb.endpoints.kb_items import ns as kb_items_namespace
from skf.api.restplus import api
from skf.database import db

app = Flask(__name__)
bcrypt = Bcrypt(app)
logging.config.fileConfig('logging.conf')
log = logging.getLogger(__name__)


def configure_app(flask_app):
    flask_app.config['SERVER_NAME'] = settings.FLASK_SERVER_NAME
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP


def initialize_app(flask_app):
    configure_app(flask_app)
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)
    api.add_namespace(users_activate_namespace)
    api.add_namespace(kb_items_namespace)
    flask_app.register_blueprint(blueprint)
    db.init_app(flask_app)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(os.path.join(app.root_path, 'db.sqlite'))
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = connect_db()
    with app.open_resource(os.path.join(app.root_path, 'db.sqlite_test'), mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.cli.command('initdb')
def initdb_command():
    """Creates the database."""
    init_md("knowledge_base")
    init_db()
    print('Initialized the database.')


def init_md(markdown_dir):
    """Converts markdown kb items"""
    kb_dir = os.path.join(app.root_path, 'markdown/'+markdown_dir)
    if markdown_dir == "knowledge_base":
        for filename in os.listdir(kb_dir):
            if filename.endswith(".md"):
                name_raw = filename.split("-")
                title = name_raw[3].replace("_", " ")
                file = os.path.join(kb_dir, filename)
                data = open(file, 'r')
                file_content = data.read()
                data.close()
                content_escaped = file_content.translate(str.maketrans({
                                              "'":  r"''",
                                              "\n": r"NEWLINE"}))
                query = "INSERT OR REPLACE INTO kb_items (content, title) VALUES ('"+content_escaped+"', '"+title+"'); \n"
                with open(os.path.join(app.root_path, 'db.sqlite_test'), 'a') as myfile:
                    myfile.write(query)
    elif markdown_dir == "checklists":
        #do checklists transform
        print("do checklists transform")
    print('Initialized the markdown to database.')


def main():
    initialize_app(app)
    log.info('>>>>> Starting development server at http://{}/api/ <<<<<'.format(app.config['SERVER_NAME']))
    app.run(debug=settings.FLASK_DEBUG)


if __name__ == "__main__":
    main()
