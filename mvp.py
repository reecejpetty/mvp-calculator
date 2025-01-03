import argparse
import csv
import sys
import player_game_log as p


class Player:
    def __init__(self, name, w, l, cmp, att, pass_yd, pass_td, ints, rush_yd, rush_td, fum, sacks):
        self.name = name
        self.cmp = cmp
        self.att = att
        self.pass_yd  = pass_yd
        self.pass_td = pass_td
        self.ints = ints
        self.rush_yd = rush_yd
        self.rush_td = rush_td
        self.fum = fum
        self.sacks = sacks
        self.wins = w
        self.losses = l
        self.rtg = self.calc_rtg()
        self.rec = f"{self.wins}-{self.losses}"
        
        # Advanced stats
        self.cmppercent = round(cmp/att*100, 1)
        self.ttl_yd = self.pass_yd + self.rush_yd
        self.ttl_td = self.pass_td + self.rush_td
        self.turnovers = self.ints + self.fum
        self.yds_game = round(self.ttl_yd / (self.wins + self.losses), 1)
        self.tds_game = round(self.ttl_td / (self.wins + self.losses), 1)
        self.tos_game = round(self.turnovers / (self.wins + self.losses), 1)
        self.tds_to = round(self.ttl_td / self.turnovers, 1)
        self.sacks_game = round(self.sacks / (self.wins + self.losses), 1)

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
    parser.add_argument("-y", default=2024, help="Year to check stats", type=int)
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

    # For each name given, attempt to scrape player's stats. Erroneous entries are mentioned and then passed, and are not included in output.
    for name in names:
        try:
            game_log = p.get_player_game_log(player = name, position = 'QB', season = year)
            pass_yd = game_log["pass_yds"].sum()
            pass_td = game_log["pass_td"].sum()
            ints = game_log["int"].sum()
            rush_yd = game_log["rush_yds"].sum()
            rush_td = game_log["rush_td"].sum()
            result_counts = game_log["result"].value_counts()
            wins = result_counts.get('W', 0)
            losses = result_counts.get('L', 0)
            fum = game_log["fumbles_lost"].sum()
            sacks = game_log["pass_sacked"].sum()
            cmp = game_log["cmp"].sum()
            att = game_log["att"].sum()
            player = Player(name, wins, losses, cmp, att, pass_yd, pass_td, ints, rush_yd, rush_td, fum, sacks)
            players.append(player)
        except IndexError:
            print(f"'{name}' is not compatible. Please use both first and last name.")
            pass
        except AttributeError:
            print(f"'{name}' was not found. Please use both first and last name.")
            pass
        except:
            print(f"'{name}' was not found or there is a bug in the code.")
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