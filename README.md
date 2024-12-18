# mvp-calculator
I made this to calculate total stats (passing + rushing) for a given set of QBs. I made this as a simply project to practice Python and save me some time finding and tracking this information myself every week.

I used some code (player_game_log.py) from user mjk2244's project https://github.com/mjk2244/pro-football-reference-web-scraper. I just added code on lines 107 and 145-148 to scrape fumbles lost as well as the other data. 

USAGE:

Enter as many QB names as you want to scrape their information, which will be sorted in order from most total yards to least by default. You must use the name used on PFR's website.

Optional Parameters:
-s Sort | Sort players by 'yds', 'tds', 'tos', 'rtg', 'rec'.
-o Output | Save additional data to a .csv (filename must end with .csv)
-y Year | Set the year to track stats. Default is 2024.
