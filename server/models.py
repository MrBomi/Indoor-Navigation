from server.extensions import db


class Building(db.Model):
    __tablename__ = 'buildings'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(20))
    address = db.Column(db.String(100))

class Floor(db.Model):
    __tablename__ = 'floor'
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
    __tablename__ = 'doors'
    id = db.Column(db.Integer, primary_key=True)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    scale_x = db.Column(db.Float)
    scale_y = db.Column(db.Float)
    name = db.Column(db.String)
    floor_id = db.Column(db.Text, nullable=False)
    building_id = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['floor_id', 'building_id'],
            ['floor.id', 'floor.building_id']
        ),
    )


class Graph(db.Model):
    __tablename__ = 'graphs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    floor_id = db.Column(db.Text, nullable=False)
    building_id = db.Column(db.Integer, nullable=False)
    json_data = db.Column(db.Text)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['floor_id', 'building_id'],
            ['floor.id', 'floor.building_id']
        ),
    )
