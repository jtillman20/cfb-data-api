from statistics import mean
from typing import Union

from sqlalchemy_utils import ScalarListType

from app import db
from scraper import SportsReferenceScraper
from .record import Record
from .team import Team


class APPoll(db.Model):
    __tablename__ = 'ap_poll'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    weeks = db.Column(db.Integer, nullable=False)
    weeks_top_ten = db.Column(db.Integer, nullable=False)
    weeks_top_five = db.Column(db.Integer, nullable=False)
    weeks_number_one = db.Column(db.Integer, nullable=False)
    preseason_ranking = db.Column(ScalarListType(int))
    final_ranking = db.Column(ScalarListType(int))
    score = db.Column(db.Integer, nullable=False)

    @property
    def preseason(self) -> int:
        if isinstance(self.preseason_ranking, list):
            return len([ranking for ranking in self.preseason_ranking
                        if ranking is not None])
        return 0

    @property
    def preseason_top_ten(self) -> int:
        if isinstance(self.preseason_ranking, list):
            return len([ranking for ranking in self.preseason_ranking
                        if ranking is not None and ranking <= 10])
        return 0

    @property
    def preseason_top_five(self) -> int:
        if isinstance(self.preseason_ranking, list):
            return len([ranking for ranking in self.preseason_ranking
                        if ranking is not None and ranking <= 5])
        return 0

    @property
    def preseason_number_one(self) -> int:
        if isinstance(self.preseason_ranking, list):
            return len([ranking for ranking in self.preseason_ranking
                        if ranking == 1])
        return 0

    @property
    def avg_preseason(self) -> Union[float, None]:
        if isinstance(self.preseason_ranking, list):
            preseason = [ranking for ranking in self.preseason_ranking
                         if ranking is not None]
            if preseason:
                return mean(preseason)
        return None

    @property
    def final(self) -> int:
        if isinstance(self.final_ranking, list):
            return len([ranking for ranking in self.final_ranking
                        if ranking is not None])
        return 0

    @property
    def final_top_ten(self) -> int:
        if isinstance(self.final_ranking, list):
            return len([ranking for ranking in self.final_ranking
                        if ranking is not None and ranking <= 10])
        return 0

    @property
    def final_top_five(self) -> int:
        if isinstance(self.final_ranking, list):
            return len([ranking for ranking in self.final_ranking
                        if ranking is not None and ranking <= 5])
        return 0

    @property
    def final_number_one(self) -> int:
        if isinstance(self.final_ranking, list):
            return len([ranking for ranking in self.final_ranking
                        if ranking == 1])
        return 0

    @property
    def avg_final(self) -> Union[float, None]:
        if isinstance(self.final_ranking, list):
            final = [ranking for ranking in self.final_ranking
                     if ranking is not None]
            if final:
                return mean(final)
        return None

    def __add__(self, other: 'APPoll') -> 'APPoll':
        """
        Add two APPoll objects to combine multiple years of data.

        Args:
            other (APPoll): Data about a team's AP Poll rankings

        Returns:
            APPoll: self
        """
        self.year = other.year
        self.weeks += other.weeks
        self.weeks_top_ten += other.weeks_top_ten
        self.weeks_top_five += other.weeks_top_five
        self.weeks_number_one += other.weeks_number_one
        self.score += other.score

        if self.preseason_ranking is not None:
            if other.preseason_ranking is not None:
                self.preseason_ranking += other.preseason_ranking
        else:
            if other.preseason_ranking is not None:
                self.preseason_ranking = other.preseason_ranking

        if self.final_ranking is not None:
            if other.final_ranking is not None:
                self.final_ranking += other.final_ranking
        else:
            if other.final_ranking is not None:
                self.final_ranking = other.final_ranking

        return self

    def __getstate__(self) -> dict:
        avg_preseason = round(self.avg_preseason, 2) \
            if self.avg_preseason is not None else self.avg_preseason
        avg_final = round(self.avg_final, 2) \
            if self.avg_final is not None else self.avg_final

        data = {
            'id': self.id,
            'year': self.year,
            'team': self.team.serialize(year=self.year),
            'weeks': self.weeks,
            'weeks_top_ten': self.weeks_top_ten,
            'weeks_top_five': self.weeks_top_five,
            'weeks_number_one': self.weeks_number_one,
            'preseason_ranking': self.preseason_ranking,
            'preseason': self.preseason,
            'preseason_top_ten': self.preseason_top_ten,
            'preseason_top_five': self.preseason_top_five,
            'preseason_number_one': self.preseason_number_one,
            'avg_preseason': avg_preseason,
            'final_ranking': self.final_ranking,
            'final': self.final,
            'final_top_ten': self.final_top_ten,
            'final_top_five': self.final_top_five,
            'final_number_one': self.final_number_one,
            'avg_final': avg_final,
            'score': self.score
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


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
    def get_final_week(cls, year: int) -> list[int]:
        """
        Get the final week numbers for the rankings for the given year.

        Args:
            year (int): Year to get final week

        Returns:
            list[int]: Final week number
        """
        query = cls.query.filter_by(year=year).with_entities(
            cls.week).distinct()
        return max([week.week for week in query])

    @classmethod
    def get_rankings(cls, year: int, week: int = None,
                     team: str = None) -> list['APPollRanking']:
        """
        Get AP Poll rankings for a given year. If week is provided,
        only get rankings for that week. If team is provided, only get
        rankings for that team.

        Args:
            year (int): Year to get rankings
            week (int): Week to get rankings
            team (str): Team for which to get rankings

        Returns:
            list[APPollRanking]: AP Poll rankings for one year, rankings
                for one week, and/or rankings for one team
        """
        query = cls.query.filter_by(year=year)

        if week is not None:
            query = query.filter_by(week=week)

        if team is not None:
            query = query.join(Team).filter_by(name=team)

        return query.all()

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
