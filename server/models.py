from server.extensions import db

class Building(db.Model):
    __tablename__ = 'buildings'
    id = db.Column(db.Text, primary_key=True)
    svg_data = db.Column(db.Text) 
    grid_svg = db.Column(db.Text) 
    x_min = db.Column(db.Float)
    x_max = db.Column(db.Float)
    y_min = db.Column(db.Float)
    y_max = db.Column(db.Float)
    doors = db.relationship('Door', backref='building', cascade='all, delete-orphan')
    graph = db.relationship('Graph', uselist=False, backref='building')


class Door(db.Model):
    __tablename__ = 'doors'
    id = db.Column(db.Text, primary_key=True)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    scale_x = db.Column(db.Float)
    scale_y = db.Column(db.Float)
    name = db.Column(db.String)
    building_id = db.Column(db.Text, db.ForeignKey('buildings.id'))


class Graph(db.Model):
    __tablename__ = 'graphs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    building_id = db.Column(db.Text, db.ForeignKey('buildings.id'))
    json_data = db.Column(db.Text)
