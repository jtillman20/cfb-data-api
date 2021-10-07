from app import db
from scraper import SportsReferenceScraper
from .record import Record
from .team import Team


class APPollRanking(db.Model):
    __tablename__ = 'ap_poll_ranking'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    first_place_votes = db.Column(db.Integer, nullable=False)
    previous_rank = db.Column(db.Integer, nullable=True)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    ties = db.Column(db.Integer, nullable=False)

    @classmethod
    def add_rankings(cls, start_year: int, end_year: int) -> None:
        """
        Get weekly AP Poll rankings for every week for the given
        years and add them to the database.

        Args:
            start_year (int): Year to start adding rankings
            end_year (int): Year to stop adding rankings
        """
        for year in range(start_year, end_year + 1):
            print(f'Adding AP Poll rankings for {year}')
            cls.add_rankings_for_one_year(year=year)

    @classmethod
    def add_rankings_for_one_year(cls, year: int) -> None:
        """
        Get weekly AP Poll rankings for every week for one year
        and add them to the database.

        Args:
            year (int): Year to add rankings
        """
        rankings = []
        scraper = SportsReferenceScraper()

        html_content = scraper.get_html_data(path=f'{year}-polls.html')
        ranking_data = scraper.parse_ap_rankings_data(html_content=html_content)

        for ranking in ranking_data:
            team = Team.query.filter_by(name=ranking['team']).first()

            if ranking['week'] == ranking['final_week'] and year < 2010:
                record = Record.get_records(start_year=year, team=team.name)
                wins = record.wins
                losses = record.losses
                ties = record.ties
            else:
                wins = ranking['wins']
                losses = ranking['losses']
                ties = ranking['ties']

            rankings.append(cls(
                year=year,
                team_id=team.id,
                week=ranking['week'],
                rank=ranking['rank'],
                first_place_votes=ranking['first_place_votes'],
                previous_rank=ranking['previous_rank'],
                wins=wins,
                losses=losses,
                ties=ties
            ))

        for ranking in sorted(rankings, key=lambda item: item.week):
            db.session.add(ranking)

        db.session.commit()

    def __getstate__(self) -> dict:
        return {
            'id': self.id,
            'year': self.year,
            'team': self.team.serialize(year=self.year),
            'week': self.week,
            'rank': self.rank,
            'points': self.points,
            'first_place_votes': self.first_place_votes,
            'previous_rank': self.previous_rank,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties
        }
