from server.extensions import db


class Building(db.Model):
    _tablename_ = 'buildings'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(20))
    address = db.Column(db.String(100))

class Floor(db.Model):
    _tablename_ = 'floor'
    id = db.Column(db.Text, nullable=False)
    svg_data = db.Column(db.Text) 
    grid_svg = db.Column(db.Text) 
    x_min = db.Column(db.Float)
    x_max = db.Column(db.Float)
    y_min = db.Column(db.Float)
    y_max = db.Column(db.Float)
    doors = db.relationship('Door', backref='building', cascade='all, delete-orphan')
    graph = db.relationship('Graph', uselist=False, backref='building')
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)
    
    __table_args__ = (
        db.PrimaryKeyConstraint('id', 'building_id'),
    )


class Door(db.Model):
    _tablename_ = 'doors'
    id = db.Column(db.Integer, primary_key=True)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    scale_x = db.Column(db.Float)
    scale_y = db.Column(db.Float)
    name = db.Column(db.String)
    floor_id = db.Column(db.Text, nullable=False)
    building_id = db.Column(db.Integer, nullable=False)

    _table_args_ = (
        db.ForeignKeyConstraint(
            ['floor_id', 'building_id'],
            ['floor.id', 'floor.building_id']
        ),
    )


class Graph(db.Model):
    _tablename_ = 'graphs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    floor_id = db.Column(db.Text, nullable=False)
    building_id = db.Column(db.Integer, nullable=False)
    json_data = db.Column(db.Text)

    _table_args_ = (
        db.ForeignKeyConstraint(
            ['floor_id', 'building_id'],
            ['floor.id', 'floor.building_id']
        ),
    )

