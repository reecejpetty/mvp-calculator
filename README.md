# MVP Calculator
I made this to calculate total stats (passing + rushing + receiving) for a given set of NFL players. I made this as a simply project to practice Python and save me some time finding and tracking this information myself every week.

Uses nflreadpy library for all data. 

USAGE:

Enter as many player names as you want to fetch their information, which will be sorted in order from most total yards to least by default. You must use the player's offical name (cap-sensitive).

Optional Parameters:
-s Sort | Sort players by 'yds', 'tds', 'tos', 'rtg', 'rec'.
-o Output | Save additional data to a .csv (filename must end with .csv)
-y Year | Set the year to track stats. Default is current year.
