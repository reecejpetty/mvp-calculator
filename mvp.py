import argparse
import csv
import sys
import nflreadpy as nfl
import polars as pl
from datetime import datetime


class Player:
    def __init__(self, stats, name, year):
        self.name = name
        self.stats = stats
        self.season = year
        self.team = (stats['team'].to_list()[:1] or [None])[0]
        self.weeks_played = stats['week'].to_list()
        self.cmp = sum(stats['completions'].to_list())
        self.att = sum(stats['attempts'].to_list())
        self.pass_yd  = sum(stats['passing_yards'].to_list())
        self.pass_td = sum(stats['passing_tds'].to_list())
        self.ints = sum(stats['passing_interceptions'].to_list())
        self.rush_yd = sum(stats['rushing_yards'].to_list())
        self.rush_td = sum(stats['rushing_tds'].to_list())
        self.fum = sum(stats['sack_fumbles_lost'].to_list()) + sum(stats['rushing_fumbles_lost'].to_list())
        self.sacks = sum(stats['sacks_suffered'].to_list())
        self.games_played = len(stats['week'].to_list())
        self.wins = self.get_outcomes('w')
        self.losses = self.get_outcomes('l')
        self.ties = self.get_outcomes('t')
        self.rec = f"{self.wins}-{self.losses}-{self.ties}"
        
        # Advanced stats
        self.ttl_yd = self.pass_yd + self.rush_yd
        self.ttl_td = self.pass_td + self.rush_td
        self.turnovers = self.ints + self.fum
    
    # Return 0s for various properties to prevent divide by 0 error
    @property
    def cmppercent(self):
        return round(self.cmp/self.att*100, 1) if self.att > 0 else 0
    
    @property
    def yds_game(self):
        return round(self.ttl_yd / self.games_played, 1) if self.games_played > 0 else 0
    
    @property
    def tds_game(self):
        return round(self.ttl_td / self.games_played, 1) if self.games_played > 0 else 0
    
    @property
    def tos_game(self):
        return round(self.turnovers / self.games_played, 1) if self.games_played > 0 else 0
    
    @property
    def sacks_game(self):
        return round(self.sacks / self.games_played, 1) if self.games_played > 0 else 0
    
    @property
    def tds_to(self):
        turnovers = 1 if self.turnovers == 0 else self.turnovers
        return round(self.ttl_td / turnovers, 1)

    @property
    def rtg(self):
        # Calculate passer rating. Return 0 if no attemps to prevent divide by 0 error
        if self.att <= 0:
            return 0
        a = ((self.cmp/self.att) - 0.3) * 5
        b = ((self.pass_yd/self.att) - 3) * 0.25
        c = (self.pass_td/self.att) * 20
        d = 2.375 - ((self.ints/self.att) * 25)
        calcs = [a, b, c, d]
        for index, value in enumerate(calcs):
            if value > 2.375:
                calcs[index] = 2.375
            elif value < 0:
                calcs[index] = 0
        return round(((sum(calcs)) / 6) * 100, 1)

    def __str__(self):
        return f"{bold(self.name):23} | {self.cmppercent}% | {self.ttl_yd:,} YDs | {self.ttl_td:2} TDs | {self.turnovers:2} TOs | {self.rtg:5} Rtg | {bold("Record:")} {self.rec:5}"

    def get_outcomes(self, outcome):
        # If no teams found (i.e. no games played), return 0
        if not self.team:
            return 0

        schedules = nfl.load_schedules([self.season])
        
        home_games = schedules.filter(pl.col('home_team') == self.team)
        away_games = schedules.filter(pl.col('away_team') == self.team)
        
        wins = 0
        losses = 0
        ties = 0

        for row in home_games.iter_rows(named=True):
            if row['week'] in self.weeks_played:
                if row['home_score'] > row['away_score']:
                    wins += 1
                elif row['home_score'] < row['away_score']:
                    losses += 1
                else:
                    ties += 1

        for row in away_games.iter_rows(named=True):
            if row['week'] in self.weeks_played:
                if row['away_score'] > row['home_score']:
                    wins += 1
                elif row['away_score'] < row['home_score']:
                    losses += 1
                else:
                    ties += 1

        match outcome:
            case 'w':
                return wins
            case 'l':
                return losses
            case 't':
                return ties


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="QB Stats Calculator")
    parser.add_argument("-s", default="yds", help="Sort by ('yds', 'tds', 'tos', 'rtg', 'rec')", type=str)
    parser.add_argument("-o", default="", help="Output to .csv", type=str)
    parser.add_argument("-y", default=datetime.now().year, help="Year to check stats", type=int)
    args = parser.parse_args()
    sort_method = args.s
    if not args.o == "" and not args.o.lower().endswith(".csv"):
        sys.exit("Invalid output. Please save as a .csv file.")
    output = args.o
    year = args.y

    names = []
    players = []

    while True:
        name = input("Player Name: ").title()
        if not name == "":
            names.append(name)
        else:
            break

    player_stats = nfl.load_player_stats([year])
    
    # For each name given, attempt to scrape player's stats. Erroneous entries are mentioned and then passed, and are not included in output.
    for name in names:
        stats = player_stats.filter(
            (pl.col('player_display_name') == name) & (pl.col('season_type') == 'REG')
        )
        player = Player(stats, name, year)
        players.append(player)
    
    sorted_players = player_sort(players, sort_method)
    
    # Print out the sorted players list.
    print()
    for player in sorted_players:
        print(player)
    print()

    # If user specified output file at runtime, save output to .csv file. Includes addtional stats. 
    if not output == "":
        with open(output, "w") as file:
            fieldnames = ["name",  "team_record", "completion_%", "total_yards", "yards/game", "total_tds", "tds/game", "turnovers", "turnovers/game", "tds/turnover", "passer_rating", "sacks", "sacks/game"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for player in sorted_players:
                writer.writerow({
                    "name": player.name,
                    "team_record": player.rec,
                    "completion_%": player.cmppercent,
                    "total_yards": player.ttl_yd,
                    "yards/game": player.yds_game,
                    "total_tds": player.ttl_td,
                    "tds/game": player.tds_game,
                    "turnovers": player.turnovers,
                    "turnovers/game": player.tos_game,
                    "tds/turnover": player.tds_to,
                    "passer_rating": player.rtg,
                    "sacks": player.sacks,
                    "sacks/game": player.sacks_game
                    })
        print(f"Advanced stats saved to '{output}'")


def bold(s):
    # Bold a given string. Seems to only work on MacOS (possibly Linux). Uncomment below line and comment out original line to fix on Windows.
    #return s
    return f"\033[1m{s}\033[0m"


def player_sort(players, sort_method):
    # Sort players list based on sort method chosen at runtime. Default is "yds"
    match sort_method:
        case "yds":
            return sorted(players, key=lambda player: player.ttl_yd, reverse=True)
        case "tds":
            return sorted(players, key=lambda player: player.ttl_td, reverse=True)
        case "tos":
            return sorted(players, key=lambda player: player.turnovers)
        case "rtg":
            return sorted(players, key=lambda player: player.rtg, reverse=True)
        case "rec":
            return sorted(players, key=lambda player: int(player.wins), reverse=True)
        case _:
            sys.exit("Incompatible sort method. Type -h to see options.")


if __name__ == "__main__":
    main()