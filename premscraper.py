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
import numpy as np
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
    seasonYrs = np.array([])
    for link in seasonURLs:
        # The current season link does not have the year
        if (link == 'https://fbref.com/en/comps/9/Premier-League-Stats'):
            seasonYrs = np.append(seasonYrs, CURRENT_SEASON)
        else:
            firstYr = getSeasonYear(link, 29, 33)
            secondYr = firstYr + 1
            seasonYrs = np.append(seasonYrs, str(firstYr) + "/" + str(secondYr))
            
    # Convert to a pandas dataframe and return
    data = pd.DataFrame(seasonYrs)
    return data

# Helper method for creating season stats. Used if the season is not missing any data.
# (all seasons starting in 2017/2018)
def createTable(seasonHTML, season):
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
    
    # Join all the tables
    seasonStats = regSeason.join(squadShooting)
    seasonStats = seasonStats.join(passingAtt)
    seasonStats = seasonStats.join(passTypes)
    seasonStats = seasonStats.join(miscStats)
    
    # Add the season years to the dataframe
    seasonYrs = []
    for i in range(0, len(seasonStats)):
        seasonYrs.append(season)
    seasonStats.insert(0, "Season", seasonYrs, True)
    
    return seasonStats

# Helper method to create a table for seasons with no passing data and missing some other data
# (1992/1993 - 2016/2017)
def createTableNoPass(seasonHTML, season):
    # Generate regular season, shooting, and misc data
    regSeason = pd.read_html(StringIO(seasonHTML), match = "Regular season Table")
    regSeason = regSeason[0]
    squadShooting = pd.read_html(StringIO(seasonHTML), match = "Squad Shooting")
    squadShooting = squadShooting[0]
    miscStats = pd.read_html(StringIO(seasonHTML), match = "Squad Miscellaneous Stats")
    miscStats = miscStats[0]
    
    # Clean the regular season data
    regSeason = regSeason[['Squad', 'W', 'D', 'L', 'GF', 'GA', 'Pts']]
    
    # Clean the shooting data
    squadShooting = squadShooting[['Standard']]
    squadShooting.columns = squadShooting.columns.droplevel(0)
    squadShooting = squadShooting[['SoT', 'PK']]
    
    # Clean the misc data
    miscStats = miscStats[['Performance']]
    miscStats.columns = miscStats.columns.droplevel(0)
    miscStats = miscStats[['CrdY', 'CrdR', 'Fls']]
    
    # Join the tables
    seasonStats = regSeason.join(squadShooting)
    seasonStats = seasonStats.join(miscStats)
    
    # Add the season years to the dataframe
    seasonYrs = []
    for i in range(0, len(seasonStats)):
        seasonYrs.append(season)
    seasonStats.insert(0, "Season", seasonYrs, True)
    
    return seasonStats

# Helper method for getSeasonStats. Gets the season stats for seasons that only have
# a regular season table (all seasons before 1992/1993)
def createRegSeasonTable(seasonHTML, season):
    # Generate the regular season dataframe
    regSeason = pd.read_html(StringIO(seasonHTML), match = "Regular season Table")
    regSeason = regSeason[0]
    
    # Clean the data
    regSeason = regSeason[['Squad', 'W', 'D', 'L', 'GF', 'GA', 'Pts']]
    
    # Add the season years to the dataframe
    seasonYrs = []
    for i in range(0, len(regSeason)):
        seasonYrs.append(season)
    regSeason.insert(0, "Season", seasonYrs, True)
    
    return regSeason
    
    
# Go through each link and get the season stats for each team
def getSeasonStats(seasonURLs):
    # Create a dataframe to store all the season stats
    allStats = pd.DataFrame()
    for link in seasonURLs:
        # Generate the HTML for each link
        seasonHTML = requests.get(link).text
        
        # Get the season years
        if (link == 'https://fbref.com/en/comps/9/Premier-League-Stats'):
            season = CURRENT_SEASON
            firstYr = 2023
        else:
            firstYr = getSeasonYear(link, 29, 33)
            secondYr = firstYr + 1
            season = str(firstYr) + "/" + str(secondYr)

        print("Getting Stats for " + season)
        # Create the stats for all season starting in 2017/2018
        if (firstYr >= 2017):
            seasonStats = createTable(seasonHTML, season)
            time.sleep(1)
        # Create season stats for seasons between 1992/1993 and 2016/2017
        elif (firstYr >= 1992):
            seasonStats = createTableNoPass(seasonHTML, season)
            time.sleep(1)
        # Create season stats for the rest of the seasons
        else:
            seasonStats = createRegSeasonTable(seasonHTML, season)
            time.sleep(1)
        
        allStats = allStats._append(seasonStats)
    return allStats

# Stores all the unique teams in an array before converting to a pandas dataframe.
def getUniqueTeams(seasonStats):
    # Get all unique teams from the season stats
    uniqueTeams = np.array([])
    teams = seasonStats['Squad'].values
    for team in teams:
        if (team not in uniqueTeams):
            print(team)
            uniqueTeams = np.append(uniqueTeams, team)
    
    # Convert the array to a pandas dataframe and return the dataframe
    data = pd.DataFrame(uniqueTeams)
    return data
            
def main():
    # Get the season links
    print("Creating Season URLs")
    seasonURLs = createSeasonLinks()
    print("SeasonURLs Created")
    
    # Get the season years
    print("Getting Season Years")
    seasonYrs = getSeasonYrs(seasonURLs)
    seasonYrs.to_csv("seasons.csv")
    print("Season Years Gathered")
    
    # Get the season stats
    print("Getting Season Stats")
    seasonStats = getSeasonStats(seasonURLs)
    seasonStats.to_csv("seasonstats.csv")
    print("Season Stats Gathered")
    
    # Get list of unique teams
    print("Getting list of unique teams")
    teams = getUniqueTeams(seasonStats)
    teams.to_csv("teams.csv")
    print("All Unique Teams Found")
        
if (__name__ == "__main__"):
    main()