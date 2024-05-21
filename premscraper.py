# Author - Evan Gora
#
# A web scraper that scrapes various different Premier League data from fbref.com
# and adds it to different CSV files. The dataset itself is downloadable from kaggle
# at: ADD LINK HERE. The data includes different stats for each team in each season 
# as well as match results from each season since the 1888/1889 season.

from io import StringIO
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time
import pandas as pd
from pip._vendor import requests

# Define the current teams and the current season
CURRENT_TEAMS = ["Manchester City", "Arsenal", "Liverpool", "Aston Villa", "Tottenham Hotspur", 
                "Newcastle Untied", "Manchester United", "West Ham United", "Chelsea", "Brighton and Hove Albion", 
                "Wolverhampton Wanderers", "Fulham", "Bournemouth", "Crystal Palace", "Brentford", "Everton", 
                "Nottingham Forest", "Luton Town", "Burnley", "Sheffield United"]

CURRENT_SEASON = "2023/2024"

# Get the name of a team from a link and an index
def getTeamName(link, indx):
    team = link[indx:]
    # Clean the string so it includes only the string
    team = team.replace("-Stats","").replace("-", " ")
    return team

# Get the first year from a link using 2 indices. (ex. if the season is 2007-2008, method will return 2007)
def getSeasonYear(link, indx1, indx2):
    year = link[indx1:indx2]
    return int(year)

# Get all of the links for each season since 1992/1993
def createSeasonLinks():
    # Open the URL with all seasons and get the HTML
    seasonsURL = "https://fbref.com/en/comps/9/history/Premier-League-Seasons"
    seasonsHTML = urlopen(seasonsURL)
    soup = BeautifulSoup(seasonsHTML, "html.parser")
    
    # Get all links from the page
    seasons = soup.findAll("a")
    seasons = [link.get("href") for link in seasons]
    # Filter the links to only have links for premier league seasons
    seasons = [link for link in seasons if type(link) == str]
    seasons = [link for link in seasons if '/en/comps/9/' in link and 'Premier-League-Stats' in link]
    # Remove duplicate links and add the fbref tag to the front
    seasonURLs = []
    for link in seasons:
        link = "https://fbref.com" + link
        if link not in seasonURLs:
            seasonURLs.append(link)
    
    return seasonURLs

# Go through each link in the seasonURLs and extract the year from them. Add the year to its own array
def getSeasonYrs(seasonURLs):
    seasonYrs = []
    for link in seasonURLs:
        # The current season link does not have the year
        if (link == 'https://fbref.com/en/comps/9/Premier-League-Stats'):
            seasonYrs.append(CURRENT_SEASON)
        else:
            firstYr = getSeasonYear(link, 29, 33)
            secondYr = firstYr + 1
            seasonYrs.append(str(firstYr) + "/" + str(secondYr))
            
    return seasonYrs

# Helper method for creating season stats. Used if the season contains passing data
# (all seasons starting in 2017/2018).
def createTables(seasonHTML, season):
    # Generate the regular season, shooting, passing, and misc data
    regSeason = pd.read_html(StringIO(seasonHTML), match = "Regular season Table")
    regSeason = regSeason[0]
    squadShooting = pd.read_html(StringIO(seasonHTML), match = "Squad Shooting")
    squadShooting = squadShooting[0]
    passingAtt = pd.read_html(StringIO(seasonHTML), match = "Squad Passing")
    passingAtt = passingAtt[0]
    passTypes = pd.read_html(StringIO(seasonHTML), match = "Squad Pass Types")
    passTypes = passTypes[0]
    miscStats = pd.read_html(StringIO(seasonHTML), match = "Squad Miscellaneous Stats")
    miscStats = miscStats[0]
    
    # Clean the regular season data
    regSeason = regSeason[['Squad', 'W', 'D', 'L', 'GF', 'GA', 'Pts']]
    
    # Clean the squad shooting data
    squadShooting = squadShooting[['Standard']]
    squadShooting.columns = squadShooting.columns.droplevel(0)
    squadShooting = squadShooting[['Sh', 'SoT', 'FK', 'PK']]
    
    # Clean the passing data
    passingAtt = passingAtt[['Total']]
    passingAtt.columns = passingAtt.columns.droplevel(0)
    passingAtt = passingAtt[['Cmp', 'Att', 'Cmp%']]
    passTypes = passTypes[['Pass Types']]
    passTypes.columns = passTypes.columns.droplevel(0)
    passTypes = passTypes[['CK']]
    
    # Clean the misc data
    miscStats = miscStats[['Performance']]
    miscStats.columns = miscStats.columns.droplevel(0)
    miscStats = miscStats[['CrdY', 'CrdR', 'Fls', 'PKcon', 'OG']]

# Go through each link and get the season stats for each team
def getSeasonStats(seasonURLs):
    for link in seasonURLs:
        # Generate the HTML for each link
        seasonHTML = requests.get(link).text
        soup = BeautifulSoup(seasonHTML, "html.parser")
        
        # Get the season years
        if (link == 'https://fbref.com/en/comps/9/Premier-League-Stats'):
            season = CURRENT_SEASON
        else:
            firstYr = getSeasonYear(link, 29, 33)
            secondYr = firstYr + 1
            season = str(firstYr) + "/" + str(secondYr)
    
def main():
    # Get the season links
    print("Creating Season URLs")
    seasonURLs = createSeasonLinks()
    print("SeasonURLs Created")
    
    # Get the season years
    print("Getting Season Years")
    seasonYrs = getSeasonYrs(seasonURLs)
    print("Season Years Gathered")
        
if (__name__ == "__main__"):
    main()