import argparse
import csv
import sys
import player_game_log as p
import nflreadpy as nfl
import polars as pl


class Player:
    def __init__(self, qb_stats):
        self.name = qb_stats.get('name')
        self.cmp = qb_stats.get('cmp')
        self.att = qb_stats.get('att')
        self.pass_yd  = qb_stats.get('pass_yd')
        self.pass_td = qb_stats.get('pass_td')
        self.ints = qb_stats.get('ints')
        self.rush_yd = qb_stats.get('rush_yd')
        self.rush_td = qb_stats.get('rush_td')
        self.fum = qb_stats.get('fum')
        self.sacks = qb_stats.get('sacks')
        self.games_played = qb_stats.get('games_played')
        self.wins = qb_stats.get('wins')
        self.losses = qb_stats.get('losses')
        self.ties = qb_stats.get('ties')
        self.rtg = self.calc_rtg()
        self.rec = f"{self.wins}-{self.losses}-{self.ties}"
        
        # Advanced stats
        self.cmppercent = round(self.cmp/self.att*100, 1)
        self.ttl_yd = self.pass_yd + self.rush_yd
        self.ttl_td = self.pass_td + self.rush_td
        self.turnovers = self.ints + self.fum
        self.yds_game = round(self.ttl_yd / self.games_played, 1)
        self.tds_game = round(self.ttl_td / self.games_played, 1)
        self.tos_game = round(self.turnovers / self.games_played, 1)
        self.sacks_game = round(self.sacks / self.games_played, 1)
    
    @property
    def tds_to(self):
        turnovers = 1 if self.turnovers == 0 else self.turnovers
        return round(self.ttl_td / turnovers, 1)

    def __str__(self):
        #return f"{bold(self.name):24} | {bold("Total YDS")}: {self.ttl_yd:,} | {bold("Total TDS:")} {self.ttl_td:2} | {bold("Turnovers:")} {self.turnovers:2} | {bold("RTG:")} {self.rtg:5} | {bold("Team Record:")} {self.rec:5}"
        return f"{bold(self.name):23} | {self.cmppercent}% | {self.ttl_yd:,} YDs | {self.ttl_td:2} TDs | {self.turnovers:2} TOs | {self.rtg:5} Rtg | {bold("Record:")} {self.rec:5}"
    
    def calc_rtg(self):
        # Calculate quarterback passer rating
        a = ((self.cmp/self.att) - 0.3) * 5
        b = ((self.pass_yd/self.att) - 3) * 0.25
        c = (self.pass_td/self.att) * 20
        d = 2.375 - ((self.ints/self.att) * 25)
        stats = [a, b, c, d]
        for stat in stats:
            if stat > 2.375:
                stat = 2.375
            elif stat < 0:
                stat = 0
        return round(((a + b + c + d) / 6) * 100, 1)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="QB Stats Calculator")
    parser.add_argument("-s", default="yds", help="Sort by ('yds', 'tds', 'tos', 'rtg', 'rec')", type=str)
    parser.add_argument("-o", default="", help="Output to .csv", type=str)
    parser.add_argument("-y", default=2026, help="Year to check stats", type=int)
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
        try:
            #game_log = p.get_player_game_log(player = name, position = 'QB', season = year)
            qb = player_stats.filter(
                (pl.col('player_display_name') == name) & (pl.col('season_type') == 'REG')
            )
            qb_stats = {}
            qb_stats['name'] = name
            qb_stats['pass_yd'] = qb.select(pl.sum('passing_yards')).item()
            qb_stats['pass_td'] = qb.select(pl.sum('passing_tds')).item()
            qb_stats['ints'] = qb.select(pl.sum('passing_interceptions')).item()
            qb_stats['rush_yd'] = qb.select(pl.sum('rushing_yards')).item()
            qb_stats['rush_td'] = qb.select(pl.sum('rushing_tds')).item()
            qb_stats['games_played'] = len(qb['week'].to_list())
            qb_stats['wins'] = get_outcomes('Wins', qb, year)
            qb_stats['losses'] = get_outcomes('Losses', qb, year)
            qb_stats['ties'] = get_outcomes('Ties', qb, year)
            qb_stats['fum'] = qb.select(pl.sum('sack_fumbles_lost')).item() + qb.select(pl.sum('rushing_fumbles_lost')).item()
            qb_stats['sacks'] = qb.select(pl.sum('sacks_suffered')).item()
            qb_stats['cmp'] = qb.select(pl.sum('completions')).item()
            qb_stats['att'] = qb.select(pl.sum('attempts')).item()
            player = Player(qb_stats)
            players.append(player)
        except IndexError:
            print(f"'{name}' is not compatible. Please use both first and last name.")
            pass
        except AttributeError:
            print(f"'{name}' was not found. Please use both first and last name.")
            pass
    
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


def get_outcomes(outcome, qb, year):
    team = qb['team'].to_list()[0]
    weeks_played = qb['week'].to_list()

    schedules = nfl.load_schedules([year])
    
    home_games = schedules.filter(pl.col('home_team') == team)
    away_games = schedules.filter(pl.col('away_team') == team)
    
    wins = 0
    losses = 0
    ties = 0

    for row in home_games.iter_rows(named=True):
        if row['week'] in weeks_played:
            if row['home_score'] > row['away_score']:
                wins += 1
            elif row['home_score'] < row['away_score']:
                losses += 1
            else:
                ties += 1

    for row in away_games.iter_rows(named=True):
        if row['week'] in weeks_played:
            if row['away_score'] > row['home_score']:
                wins += 1
            elif row['away_score'] < row['home_score']:
                losses += 1
            else:
                ties += 1

    match outcome:
        case 'Wins':
            return wins
        case 'Losses':
            return losses
        case 'Ties':
            return ties

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