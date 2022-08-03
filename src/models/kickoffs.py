from operator import attrgetter

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team


class Kickoffs(db.Model):
    __tablename__ = 'kickoffs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    kickoffs = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    touchbacks = db.Column(db.Integer, nullable=False)
    out_of_bounds = db.Column(db.Integer, nullable=False)
    onside = db.Column(db.Integer, nullable=False)

    @property
    def yards_per_kickoff(self) -> float:
        if self.kickoffs:
            return self.yards / self.kickoffs
        return 0.0

    @property
    def touchback_pct(self) -> float:
        if self.kickoffs:
            return self.touchbacks / self.kickoffs * 100
        return 0.0

    @property
    def out_of_bounds_pct(self) -> float:
        if self.kickoffs:
            return self.out_of_bounds / self.kickoffs * 100
        return 0.0

    @property
    def onside_pct(self) -> float:
        if self.kickoffs:
            return self.onside / self.kickoffs * 100
        return 0.0

    @classmethod
    def get_kickoffs(cls, side_of_ball: str, start_year: int,
                     end_year: int = None, team: str = None
                     ) -> list['Kickoffs']:
        """
        Get kickoffs or opponent kickoffs for qualifying teams for the
        given years. If team is provided, only get kickoff data for
        that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting kickoff data
            end_year (int): Year to stop getting kickoff data
            team (str): Team for which to get kickoff data

        Returns:
            list[Kickoffs]: Kickoffs or opponent kickoffs for all teams
                or only for one team
        """
        if end_year is None:
            end_year = start_year

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            kickoffs = query.filter_by(name=team).all()
            return [sum(kickoffs[1:], kickoffs[0])] if kickoffs else []

        kickoffs = {}
        for team_name in Team.get_qualifying_teams(
                start_year=start_year, end_year=end_year):
            team_kickoffs = query.filter_by(name=team_name).all()

            if team_kickoffs:
                kickoffs[team_name] = sum(team_kickoffs[1:], team_kickoffs[0])

        return [kickoffs[team] for team in sorted(kickoffs.keys())]

    @classmethod
    def add_kickoffs(cls, start_year: int = None, end_year: int = None) -> None:
        """
        Get kickoff and opponent kickoff stats for all teams for the
        given years and add them to the database.

        Args:
            start_year (int): Year to start adding kickoff stats
            end_year (int): Year to stop adding kickoff stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding kickoff stats for {year}')
            cls.add_kickoffs_for_one_year(year=year)

    @classmethod
    def add_kickoffs_for_one_year(cls, year: int) -> None:
        """
        Get kickoff and opponent kickoff stats for all teams for
        one year and add them to the database.

        Args:
            year (int): Year to add kickoff stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            kickoffs = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='29')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()

                kickoffs.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    kickoffs=item[3],
                    yards=item[4],
                    touchbacks=item[6],
                    out_of_bounds=item[8],
                    onside=item[9]
                ))

            for team_kickoffs in sorted(kickoffs, key=attrgetter('team_id')):
                db.session.add(team_kickoffs)

        db.session.commit()

    def __add__(self, other: 'Kickoffs') -> 'Kickoffs':
        """
        Add two Kickoffs objects to combine multiple years of data.

        Args:
            other (Kickoffs): Data about a team's kickoffs or opponent
                kickoffs

        Returns:
            Kickoffs: self
        """
        self.games += other.games
        self.kickoffs += other.kickoffs
        self.yards += other.yards
        self.touchbacks += other.touchbacks
        self.out_of_bounds += other.out_of_bounds
        self.onside += other.onside

        return self

    def __getstate__(self) -> dict:
        data = {
            'id': self.id,
            'team': self.team.serialize(year=self.year),
            'year': self.year,
            'side_of_ball': self.side_of_ball,
            'games': self.games,
            'kickoffs': self.kickoffs,
            'yards': self.yards,
            'yards_per_kickoff': round(self.yards_per_kickoff, 2),
            'touchbacks': self.touchbacks,
            'touchback_pct': round(self.touchback_pct, 2),
            'out_of_bounds': self.out_of_bounds,
            'out_of_bounds_pct': round(self.out_of_bounds_pct, 2),
            'onside': self.onside,
            'onside_pct': round(self.onside_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


class KickoffReturns(db.Model):
    __tablename__ = 'kickoff_returns'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    returns = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    tds = db.Column(db.Integer, nullable=False)
    kickoffs = db.Column(db.Integer, nullable=False)

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
        if self.kickoffs:
            return self.returns / self.kickoffs * 100
        return 0.0

    @classmethod
    def get_kickoff_returns(cls, side_of_ball: str, start_year: int,
                            end_year: int = None, team: str = None
                            ) -> list['KickoffReturns']:
        """
        Get kickoff returns or opponent kickoff returns for qualifying teams
        for the given years. If team is provided, only get kickoffing  data
        for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting kickoff return data
            end_year (int): Year to stop getting kickoff return data
            team (str): Team for which to get kickoff return data

        Returns:
            list[KickoffReturns]: Kickoff returns or opponent kickoff
                returns for all teams or only for one team
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
    def add_kickoff_returns(cls, start_year: int = None,
                            end_year: int = None) -> None:
        """
        Get kickoff return and opponent kickoff return stats for all
        teams for the given years and add them to the database.

        Args:
            start_year (int): Year to start adding kickoff return stats
            end_year (int): Year to stop adding kickoff return stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding kickoff return stats for {year}')
            cls.add_kickoff_returns_for_one_year(year=year)

    @classmethod
    def add_kickoff_returns_for_one_year(cls, year: int) -> None:
        """
        Get kickoff return and opponent kickoff return stats for all teams
        for one year and add them to the database.

        Args:
            year (int): Year to add kickoff return stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            returns = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='05')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                opposite_side_of_ball = ('defense' if side_of_ball == 'offense'
                                         else 'offense')
                kickoffs = Kickoffs.query.filter_by(
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
                    kickoffs=kickoffs.kickoffs
                ))

            for team_returns in sorted(returns, key=attrgetter('team_id')):
                db.session.add(team_returns)

        db.session.commit()

    def __add__(self, other: 'KickoffReturns') -> 'KickoffReturns':
        """
        Add two KickoffReturns objects to combine multiple years of data.

        Args:
            other (KickoffReturns): Data about a team's kickoff returns
                or opponent kickoff returns

        Returns:
            KickoffReturns: self
        """
        self.games += other.games
        self.returns += other.returns
        self.yards += other.yards
        self.tds += other.tds
        self.kickoffs += other.kickoffs

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
            'kickoffs': self.kickoffs,
            'return_pct': round(self.return_pct, 2)

        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data


class KickoffReturnPlays(db.Model):
    __tablename__ = 'kickoff_return_plays'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    thirty = db.Column(db.Integer, nullable=False)
    forty = db.Column(db.Integer, nullable=False)
    fifty = db.Column(db.Integer, nullable=False)
    sixty = db.Column(db.Integer, nullable=False)
    seventy = db.Column(db.Integer, nullable=False)
    eighty = db.Column(db.Integer, nullable=False)
    ninety = db.Column(db.Integer, nullable=False)
    returns = db.Column(db.Integer, nullable=False)

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
    def get_kickoff_return_plays(cls, side_of_ball: str, start_year: int,
                                 end_year: int = None, team: str = None
                                 ) -> list['KickoffReturnPlays']:
        """
        Get kickoff return plays or opponent kickoff return plays for
        qualifying teams for the given years. If team is provided, only
        get kickoff return play data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting kickoff return play
                data
            end_year (int): Year to stop getting kickoff return play
                data
            team (str): Team for which to get kickoff return play data

        Returns:
            list[KickoffReturnPlays]: Kickoff return plays or opponent
                kickoff return plays for all teams or only for one team
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
    def add_kickoff_return_plays(cls, start_year: int = None,
                                 end_year: int = None) -> None:
        """
        Get kickoff return plays and opponent kickoff return plays for
        all teams for the given years and add them to the database.

        Args:
            start_year (int): Year to start adding kickoff return play
                stats
            end_year (int): Year to stop adding kickoff return play
                stats
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
            print(f'Adding kickoff return play stats for {year}')
            cls.add_kickoff_return_plays_for_one_year(year=year)

    @classmethod
    def add_kickoff_return_plays_for_one_year(cls, year: int) -> None:
        """
        Get kickoff return plays and opponent kickoff return plays for
        all teams for one year and add them to the database.

        Args:
            year (int): Year to add kickoff return play stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            kickoff_return_plays = []
            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='34')

            for item in scraper.parse_html_data(html_content=html_content):
                team = Team.query.filter_by(name=item[1]).first()
                returns = KickoffReturns.query.filter_by(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                ).first()

                kickoff_return_plays.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    thirty=item[3],
                    forty=item[4],
                    fifty=item[5],
                    sixty=item[6],
                    seventy=item[7],
                    eighty=item[8],
                    ninety=item[9],
                    returns=returns.returns
                ))

            for team_kickoff_return_plays in sorted(
                    kickoff_return_plays, key=attrgetter('team_id')):
                db.session.add(team_kickoff_return_plays)

        db.session.commit()

    def __add__(self, other: 'KickoffReturnPlays') -> 'KickoffReturnPlays':
        """
        Add two KickoffReturnPlays objects to combine multiple years of
        data.

        Args:
            other (KickoffReturnPlays): Data about a team's kickoff
                return plays or opponent kickoff return plays

        Returns:
            KickoffReturnPlays: self
        """
        self.games += other.games
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
