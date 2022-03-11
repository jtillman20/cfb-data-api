from operator import attrgetter
from typing import Union

from app import db
from scraper import CFBStatsScraper
from .game import Game
from .team import Team
from .total import Total


class TacklesForLoss(db.Model):
    __tablename__ = 'tackles_for_loss'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    side_of_ball = db.Column(db.String(10), nullable=False)
    games = db.Column(db.Integer, nullable=False)
    tackles_for_loss = db.Column(db.Integer, nullable=False)
    yards = db.Column(db.Integer, nullable=False)
    plays = db.Column(db.Integer, nullable=False)

    @property
    def tackles_for_loss_per_game(self) -> float:
        if self.games:
            return self.tackles_for_loss / self.games
        return 0.0

    @property
    def tackle_for_loss_pct(self) -> float:
        if self.plays:
            return self.tackles_for_loss / self.plays * 100
        return 0.0

    @property
    def yards_per_tackle_for_loss(self) -> float:
        if self.tackles_for_loss:
            return self.yards / self.tackles_for_loss
        return 0.0

    @classmethod
    def get_tackles_for_loss(cls, side_of_ball: str, start_year: int,
                             end_year: int = None, team: str = None
                             ) -> Union['TacklesForLoss',
                                        list['TacklesForLoss']]:
        """
        Get tackles for loss or opponent tackles for loss for qualifying
        teams for the given years. If team is provided, only get tackle
        for loss data for that team.

        Args:
            side_of_ball (str): Offense or defense
            start_year (int): Year to start getting tackle for loss data
            end_year (int): Year to stop getting tackle for loss data
            team (str): Team for which to get tackle for loss data

        Returns:
            Union[TacklesForLoss, list[TacklesForLoss]]: Tackles for
                loss or opponent tackles for loss for all teams or only
                for one team
        """
        if end_year is None:
            end_year = start_year

        qualifying_teams = Team.get_qualifying_teams(
            start_year=start_year, end_year=end_year)

        query = cls.query.join(Team).filter(
            cls.side_of_ball == side_of_ball,
            cls.year >= start_year,
            cls.year <= end_year
        )

        if team is not None:
            tfl = query.filter_by(name=team).all()
            return sum(tfl[1:], tfl[0])

        tfl = {}
        for team_name in qualifying_teams:
            team_tfl = query.filter_by(name=team_name).all()

            if team_tfl:
                tfl[team_name] = sum(team_tfl[1:], team_tfl[0])

        return [tfl[team] for team in sorted(tfl.keys())]

    @classmethod
    def add_tackles_for_loss(cls, start_year: int = None,
                             end_year: int = None) -> None:
        """
        Get tackles for loss and opponent tackles for loss stats for
        all teams for the given years and add them to the database.

        Args:
            start_year (int): Year to start adding tackles for loss
                stats
            end_year (int): Year to stop adding tackles for loss
                stats
        """
        if start_year is None:
            query = Game.query.with_entities(Game.year).distinct()
            years = [year.year for year in query]
        else:
            if end_year is None:
                end_year = start_year
            years = range(start_year, end_year + 1)

        for year in years:
            print(f'Adding tackles for loss stats for {year}')
            cls.add_tackles_for_loss_for_one_year(year=year)

    @classmethod
    def add_tackles_for_loss_for_one_year(cls, year: int) -> None:
        """
        Get tackles for loss and opponent tackles for loss stats for
        all teams for one year and add them to the database.

        Args:
            year (int): Year to add tackles for loss stats
        """
        scraper = CFBStatsScraper(year=year)

        for side_of_ball in ['offense', 'defense']:
            tfl = []

            html_content = scraper.get_html_data(
                side_of_ball=side_of_ball, category='21')
            tfl_data = scraper.parse_html_data(
                html_content=html_content)

            for item in tfl_data:
                team = Team.query.filter_by(name=item[1]).first()
                opposite_side_of_ball = 'defense' \
                    if side_of_ball == 'offense' else 'offense'
                total = Total.get_total(
                    side_of_ball=opposite_side_of_ball,
                    start_year=year,
                    team=team.name
                )

                tfl.append(cls(
                    team_id=team.id,
                    year=year,
                    side_of_ball=side_of_ball,
                    games=item[2],
                    tackles_for_loss=item[3],
                    yards=item[4],
                    plays=total.plays
                ))

            for team_tfl in sorted(tfl, key=attrgetter('team_id')):
                db.session.add(team_tfl)

        db.session.commit()

    def __add__(self, other: 'TacklesForLoss') -> 'TacklesForLoss':
        """
        Add two TacklesForLoss objects to combine multiple years of
        data.

        Args:
            other (TacklesForLoss): Data about a team's tackles for
                loss or opponent's tackles for loss

        Returns:
            TacklesForLoss: self
        """
        self.games += other.games
        self.tackles_for_loss += other.tackles_for_loss
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
            'tackles_for_loss': self.tackles_for_loss,
            'tackles_for_loss_per_game': round(
                self.tackles_for_loss_per_game, 2),
            'yards': self.yards,
            'yards_per_tackle_for_loss': round(
                self.yards_per_tackle_for_loss, 2),
            'plays': self.plays,
            'tackle_for_loss_pct': round(self.tackle_for_loss_pct, 2)
        }

        if hasattr(self, 'rank'):
            data['rank'] = self.rank

        return data
