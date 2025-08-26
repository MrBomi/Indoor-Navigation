from flask import Flask
from server.config import Config
from server.mangerBuldings import mangerBuldings
from server.extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        from server import models  
        
        db.create_all()
    
        from server.endPoints import bp
        app.register_blueprint(bp)

        manager = mangerBuldings()
        app.config['MANAGER'] = manager

    return app