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

    @classmethod
    def get_ap_poll_data(cls, start_year: int, end_year: int = None,
                         team: str = None) -> list['APPoll']:
        """
        Get AP Poll data for the given years. If team is provided, then
        only get data for that team.

        Args:
            start_year (int): Year to start getting poll data
            end_year (int): Year to stop getting poll data
            team (str): Team for which to get poll data

        Returns:
            list[APPoll]: AP Poll data for all teams or only poll data
                for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.year >= start_year, cls.year <= end_year)

        if team is not None:
            ap_poll = query.filter_by(name=team).all()
            return [sum(ap_poll[1:], ap_poll[0])] if ap_poll else []

        ap_poll = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_ap_poll = query.filter_by(name=team_name).all()

            if team_ap_poll:
                ap_poll[team_name] = sum(team_ap_poll[1:], team_ap_poll[0])

        return [ap_poll[team] for team in sorted(ap_poll.keys())]

    @classmethod
    def add_poll_data(cls, start_year: int = None,
                      end_year: int = None) -> None:
        """
        Get AP Poll ranking data for every team in the rankings for
        each year and add them to the database.

        Args:
            start_year (int): Year to start adding poll data
            end_year (int): Year to stop adding poll data
        """
        if start_year is None:
            query = APPollRanking.query.with_entities(
                APPollRanking.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding AP Poll data for {year}')
            cls.add_poll_data_for_one_year(year=year)

    @classmethod
    def add_poll_data_for_one_year(cls, year: int) -> None:
        """
        Get AP Poll ranking data for every team in the rankings for
        each year and add them to the database.

        Args:
            year (int): Year to add AP Poll rankings data
        """
        ap_poll = {}

        for ranking in APPollRanking.get_rankings(year=year):
            team_name = ranking.team.name
            rank = ranking.rank

            if ranking.team.name not in ap_poll:
                team_ap_poll = cls(
                    team_id=ranking.team_id,
                    year=year,
                    weeks=0,
                    weeks_top_ten=0,
                    weeks_top_five=0,
                    weeks_number_one=0,
                    score=0
                )
                ap_poll[team_name] = team_ap_poll
            else:
                team_ap_poll = ap_poll[team_name]

            team_ap_poll.weeks += 1

            if rank <= 10:
                team_ap_poll.weeks_top_ten += 1
                if rank <= 5:
                    team_ap_poll.weeks_top_five += 1
                    if rank == 1:
                        team_ap_poll.weeks_number_one += 1

            if ranking.week == 1:
                team_ap_poll.preseason_ranking = [rank]

            final_week = APPollRanking.get_final_week(year=year)
            if ranking.week == final_week:
                team_ap_poll.score = 26 - rank
                team_ap_poll.final_ranking = [rank]

        for item in sorted(ap_poll):
            db.session.add(ap_poll[item])

        db.session.commit()

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
        avg_preseason = (round(self.avg_preseason, 2)
                         if self.avg_preseason is not None else self.avg_preseason)
        avg_final = (round(self.avg_final, 2)
                     if self.avg_final is not None else self.avg_final)

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
    def get_final_week(cls, year: int) -> int:
        """
        Get the final week numbers for the rankings for the given year.

        Args:
            year (int): Year to get final week

        Returns:
            int: Final week number
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

        for ranking in scraper.parse_ap_rankings_data(
                html_content=html_content):
            team = Team.query.filter_by(name=ranking[3]).first()
            final_week = ranking[0]
            week = ranking[1]

            if week == final_week and year < 2010:
                record = Record.query.filter_by(
                    team_id=team.id, year=year).first()
                wins = record.wins
                losses = record.losses
                ties = record.ties
            else:
                wins = ranking[6]
                losses = ranking[7]
                ties = ranking[8]

            rankings.append(cls(
                year=year,
                team_id=team.id,
                week=week,
                rank=ranking[2],
                first_place_votes=ranking[4],
                previous_rank=ranking[5],
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
