from sqlalchemy_utils import ScalarListType

from app import db


class Conference(db.Model):
    __tablename__ = 'conference'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class ConferenceMembership(db.Model):
    __tablename__ = 'conference_membership'
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), primary_key=True)
    conference_id = db.Column(
        db.Integer, db.ForeignKey('conference.id'), primary_key=True)
    years = db.Column(ScalarListType(int))
    conference = db.relationship('Conference', backref='teams')
    team = db.relationship('Team', backref='conferences')
