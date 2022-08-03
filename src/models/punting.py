from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team
from .total import Total


class Punting(db.Model):
    __tablename__ = 'punting'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    punts = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def punts_per_game(self) -> float:
        if self.games:
            return self.punts / self.games
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def yards_per_punt(self) -> float:
        if self.punts:
            return self.yards / self.punts
        return 0.0

    @property
    def plays_per_punt(self) -> float:
        if self.punts:
            return self.plays / self.punts
        return 0.0

    @classmethod
    def get_punting(cls, side_of_ball: str, start_year: int,
                    end_year: int = None, team: str = None) -> list['Punting']:
        """
        Get punting or opponent punting for qualifying teams for the
        given years. If team is provided, only get punting data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting punting data
            end_year (int): Year to stop getting punting data
            team (str): Team for which to get punting data

        Returns:
            list[Punting]: Punting or opponent punting for all teams or
                only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            punting = query.filter_by(name=team).all()
            return [sum(punting[1:], punting[0])] if punting else []

        punting = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_punting = query.filter_by(name=team_name).all()

            if team_punting:
                punting[team_name] = sum(team_punting[1:], team_punting[0])

        return [punting[team] for team in sorted(punting.keys())]

    @classmethod
    def add_punting(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get punting and opponent punting stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding punting stats
            end_year (int): Year to stop adding punting stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding punting stats for {year}')
            cls.add_punting_for_one_year(year=year)

    @classmethod
    def add_punting_for_one_year(cls, year: int) -> None:
        """
        Get punting and opponent punting stats for all teams for one
        year and add them to the database.

        Args:
            year (int): Year to add punting stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            punting = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='06')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                opposite_side_of_ball = ('defense' if side_of_ball == 'offense'
                                         else 'offense')
                total = Total.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=opposite_side_of_ball,
                ).first()

                punting.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    punts=item[3],
                    yards=item[4],
                    plays=total.plays
                ))

            for team_punting in sorted(punting, key=attrgetter('team_id')):
                db.session.add(team_punting)

        db.session.commit()

    def __add__(self, other: 'Punting') -> 'Punting':
        """
        Add two Punting objects to combine multiple years of data.

        Args:
            other (Punting): Data about a team's punting or opponent
                punting

        Returns:
            Punting: self
        """
        self.games += other.games
        self.punts += other.punts
        self.yards += other.yards
        self.plays += other.plays

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'punts': self.punts,
            'punts_per_game': round(self.punts_per_game, 2),
            'yards': self.yards,
            'yards_per_game': round(self.yards_per_game, 1),
            'yards_per_punt': round(self.yards_per_punt, 2),
            'plays_per_punt': round(self.plays_per_punt, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


class PuntReturns(db.Model):
    __tablename__ = 'punt_returns'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    returns = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)
    punts = db.Column(db.Integer, nullable=False)

    @property
    def returns_per_game(self) -> float:
        if self.games:
            return self.returns / self.games
        return 0.0

    @property
    def yards_per_game(self) -> float:
        if self.games:
            return self.yards / self.games
        return 0.0

    @property
    def yards_per_return(self) -> float:
        if self.returns:
            return self.yards / self.returns
        return 0.0

    @property
    def td_pct(self) -> float:
        if self.returns:
            return self.tds / self.returns * 100
        return 0.0

    @property
    def return_pct(self) -> float:
        if self.punts:
            return self.returns / self.punts * 100
        return 0.0

    @classmethod
    def get_punt_returns(cls, side_of_ball: str, start_year: int,
                         end_year: int = None, team: str = None
                         ) -> list['PuntReturns']:
        """
        Get punt returns or opponent punt returns for qualifying teams
        for the given years. If team is provided, only get punting  data
        for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting punt return data
            end_year (int): Year to stop getting punt return data
            team (str): Team for which to get punt return data

        Returns:
            list[PuntReturns]: Punt returns or opponent punt returns for
                all teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            returns = query.filter_by(name=team).all()
            return [sum(returns[1:], returns[0])] if returns else []

        returns = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_returns = query.filter_by(name=team_name).all()

            if team_returns:
                returns[team_name] = sum(team_returns[1:], team_returns[0])

        return [returns[team] for team in sorted(returns.keys())]

    @classmethod
    def add_punt_returns(cls, start_year: int = None,
                         end_year: int = None) -> None:
        """
        Get punt return and opponent punt return stats for all teams
        for the given years and add them to the database.

        Args:
            start_year (int): Year to start adding punt return stats
            end_year (int): Year to stop adding punt return stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding punt return stats for {year}')
            cls.add_punt_returns_for_one_year(year=year)

    @classmethod
    def add_punt_returns_for_one_year(cls, year: int) -> None:
        """
        Get punt return and opponent punt return stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add punt return stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            returns = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='04')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                opposite_side_of_ball = ('defense' if side_of_ball == 'offense'
                                         else 'offense')
                punting = Punting.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=opposite_side_of_ball,
                ).first()

                returns.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    returns=item[3],
                    yards=item[4],
                    tds=item[6],
                    punts=punting.punts
                ))

            for team_returns in sorted(returns, key=attrgetter('team_id')):
                db.session.add(team_returns)

        db.session.commit()

    def __add__(self, other: 'PuntReturns') -> 'PuntReturns':
        """
        Add two PuntReturns objects to combine multiple years of data.

        Args:
            other (PuntReturns): Data about a team's punt returns or
                opponent punt returns

        Returns:
            PuntReturns: self
        """
        self.games += other.games
        self.returns += other.returns
        self.yards += other.yards
        self.tds += other.tds
        self.punts += other.punts

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'returns': self.returns,
            'returns_per_game': round(self.returns_per_game, 2),
            'yards': self.yards,
            'yards_per_game': round(self.yards_per_game, 1),
            'yards_per_return': round(self.yards_per_return, 2),
            'tds': self.tds,
            'td_pct': round(self.td_pct, 2),
            'punts': self.punts,
            'return_pct': round(self.return_pct, 2)

        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


class PuntReturnPlays(db.Model):
    __tablename__ = 'punt_return_plays'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    twenty = db.Column(db.Integer, nullable=False)
    thirty = db.Column(db.Integer, nullable=False)
    forty = db.Column(db.Integer, nullable=False)
    fifty = db.Column(db.Integer, nullable=False)
    sixty = db.Column(db.Integer, nullable=False)
    seventy = db.Column(db.Integer, nullable=False)
    eighty = db.Column(db.Integer, nullable=False)
    ninety = db.Column(db.Integer, nullable=False)
    returns = db.Column(db.Integer, nullable=False)

    @property
    def twenty_pct(self) -> float:
        if self.returns:
            return self.twenty / self.returns * 100
        return 0.0

    @property
    def thirty_pct(self) -> float:
        if self.returns:
            return self.thirty / self.returns * 100
        return 0.0

    @property
    def forty_pct(self) -> float:
        if self.returns:
            return self.forty / self.returns * 100
        return 0.0

    @property
    def fifty_pct(self) -> float:
        if self.returns:
            return self.fifty / self.returns * 100
        return 0.0

    @property
    def sixty_pct(self) -> float:
        if self.returns:
            return self.sixty / self.returns * 100
        return 0.0

    @property
    def seventy_pct(self) -> float:
        if self.returns:
            return self.sixty / self.returns * 100
        return 0.0

    @property
    def eighty_pct(self) -> float:
        if self.returns:
            return self.eighty / self.returns * 100
        return 0.0

    @property
    def ninety_pct(self) -> float:
        if self.returns:
            return self.ninety / self.returns * 100
        return 0.0

    @classmethod
    def get_punt_return_plays(cls, side_of_ball: str, start_year: int,
                              end_year: int = None, team: str = None
                              ) -> list['PuntReturnPlays']:
        """
        Get punt return plays or opponent punt return plays for qualifying
        teams for the given years. If team is provided, only get punting
        data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting punt return data
            end_year (int): Year to stop getting punt return data
            team (str): Team for which to get punt return data

        Returns:
            list[PuntReturnPlays]: Punt return plays or opponent punt
                return plays for all teams or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            returns = query.filter_by(name=team).all()
            return [sum(returns[1:], returns[0])] if returns else []

        returns = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_returns = query.filter_by(name=team_name).all()

            if team_returns:
                returns[team_name] = sum(team_returns[1:], team_returns[0])

        return [returns[team] for team in sorted(returns.keys())]

    @classmethod
    def add_punt_return_plays(cls, start_year: int = None,
                              end_year: int = None) -> None:
        """
        Get punt return plays and opponent punt return plays for all
        teams for the given years and add them to the database.

        Args:
            start_year (int): Year to start adding punt return play stats
            end_year (int): Year to stop adding punt return play stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            end_year = max([year.year for year in query])
            years = range(2010, end_year + 1)
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding punt return play stats for {year}')
            cls.add_punt_return_plays_for_one_year(year=year)

    @classmethod
    def add_punt_return_plays_for_one_year(cls, year: int) -> None:
        """
        Get punt return plays and opponent punt return plays for all
        teams for one year and add them to the database.

        Args:
            year (int): Year to add punt return play stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            punt_return_plays = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='33')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                returns = PuntReturns.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                ).first()

                punt_return_plays.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    twenty=item[3],
                    thirty=item[4],
                    forty=item[5],
                    fifty=item[6],
                    sixty=item[7],
                    seventy=item[8],
                    eighty=item[9],
                    ninety=item[10],
                    returns=returns.returns
                ))

            for team_punt_return_plays in sorted(
                    punt_return_plays, key=attrgetter('team_id')):
                db.session.add(team_punt_return_plays)

        db.session.commit()

    def __add__(self, other: 'PuntReturnPlays') -> 'PuntReturnPlays':
        """
        Add two PuntReturnPlays objects to combine multiple years of
        data.

        Args:
            other (PuntReturnPlays): Data about a team's punt return
                plays or opponent punt return plays

        Returns:
            PuntReturnPlays: self
        """
        self.games += other.games
        self.twenty += other.twenty
        self.thirty += other.thirty
        self.forty += other.forty
        self.fifty += other.fifty
        self.sixty += other.sixty
        self.seventy += other.seventy
        self.eighty += other.eighty
        self.ninety += other.ninety
        self.returns += other.returns

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'twenty': self.twenty,
            'twenty_pct': round(self.twenty_pct, 2),
            'thirty': self.thirty,
            'thirty_pct': round(self.thirty_pct, 2),
            'forty': self.forty,
            'forty_pct': round(self.forty_pct, 2),
            'fifty': self.fifty,
            'fifty_pct': round(self.fifty_pct, 2),
            'sixty': self.sixty,
            'sixty_pct': round(self.sixty_pct, 2),
            'seventy': self.seventy,
            'seventy_pct': round(self.seventy_pct, 2),
            'eighty': self.eighty,
            'eighty_pct': round(self.eighty_pct, 2),
            'ninety': self.ninety,
            'ninety_pct': round(self.ninety_pct, 2),
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
