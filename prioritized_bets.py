import numpy as np
import pandas as pd
from sportsreference.ncaab.teams import Teams
import pickle
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from numpy import loadtxt
from keras.models import Sequential
from keras.layers import Dense
import math

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpathes
from sklearn.metrics import mean_squared_error
from keras import backend as K
from keras.layers import Dropout
from sklearn.utils import shuffle
from datetime import datetime
import csv
import json
import requests
import firebase_admin
from firebase_admin import db
from datetime import datetime
#from dotenv import load_dotenv # ONLY USE LOCALLY

season = 2023

key = '54f40b3f1ece0eb377471a2c16459bf3'
#api = 'https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey='+key+'&regions=us&markets=h2h,spreads&oddsFormat=american'

# load name conversion
name_conversion_f = open('output/dk_to_sportsref.json')
name_conversion = json.load(name_conversion_f)

class CsvTextBuilder(object):
    def __init__(self):
        self.csv_string = []
    def write(self, row):
        self.csv_string.append(row)

def initFirebase():
    cred_obj = firebase_admin.credentials.Certificate({
        "type": "service_account",
        "project_id": "betquty-capital",
        "private_key_id": os.getenv("private_key_id"), #"d3085c37bb6e6df734e101c8a303c32031af6ffa",
        "private_key": os.getenv("private_key").replace("\\n", "\n"), #"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCgQTc10vKrt0Xj\n2J+fdNyNkqz3dNddLkoYbS/piNad1GAAyikm7jHAJJSQ4fe6SDnzYyawZkGHWv6B\nAdsc2TaK7Hd9FocBuhKgxoCbmQF3W3nopcbT9eR7NnoauJY0OMBlcmg+n9zFcpW/\nw+g6u+Xm8rVvZe7wAaekWXQxlY7CsG0u3J5SC6sfGrzoaFG6VEwfbH9mDIjC0AcK\n4UsWDUQ4bG/HmC/tmLuxP8qsxa6CSWU0ps10IYSCPVurOSEW86He6+RiB3W/HnG1\nKiO2+tkcTC7x7wRzH5ZjPs1tol5/XdPj3WIXFD37PFabKNgvGjbvAAGJbI7+61eE\nRblo0wLhAgMBAAECggEAIRkHDZtJWnTKPwItCZJpwOWjyqH7nveh/wSCCkIkTUmh\nIFiggjVc2hnUA05gSz2CloWKZpFgBFQjT0KyXfVwweWP0ip2bMFg+oq04i4KMvwW\nJBolA/77lwUL1/v6rcNw3SLxa8m5n6AIVKhiDMtk8rt7BIxxemllFdkR2fHRH91b\nrMa28V//RzbSS2KQkNNWGH53uTGmVyvb4fUYzXMz+MhGYcOcacS8l4r7bEHix7OG\nZ6YxkuTMX2wL3MPVxYw77iqg0Mnk5MG7mSUUgTuMn/xpPiVw6l8b8RcXMbsAVvcD\n2typRJCEyUhzV8GX2ipfDdOrfJ+hGSyCS97cATPKtwKBgQDLW5utx1SxyM//xoqi\n0uWT1UXgOCYsgt7xCAcxxq1gfmURFsN+A4bl2+iS33uBN4Amf2P6rABMARSUeTnS\ndZJ5XySumjeFIq2KQ4YpMZoSprj9MPSK0TE+AfR1DWTcgq/5hvRQkQXcjpDuRyII\nKfkHgwqTmegG16xe5wi23FqR4wKBgQDJvTGH2JJ6XltHO5cxzfe6kmhcLRbHDmA4\nFjgv8FhOjIJqjtzhjLE10nlUISBSPMtEQ+cZdXZkMworzssufVSvcmfIokP6gmK7\nOiLkmqeF2dyXno/0ZHP/xI5N9UhCM+r+T1Iqs81GTBZIp3Q+Ejt2BWNWdXCoyEfX\njmEIVcIjawKBgDgl2AsYQVNBHeUCPZ8NWeQCe+OXvTqG++VTESF2OMKuw1r/jQSL\nFsD6gfGjkOcxmsmGXOWGfiJ+Hd+MxSFN4x5t3aPz4qZ416+YSz+ueVry+5q03KBD\neDQluAhlpVaZIttjnqtsD1FBb9TKgSP96stfLBlq4jyZafdeFPLgToV/AoGBAL2o\nK+R2al64Tj/NefrMk9TGx23AxeUlUrfny7Ll1V8jIYhj/qvcxMzArme1LNmjZcUr\nwRtiHodcpHdC1ilCklbOy1sHkbj00zUJFryr2Eox4vx3iQZNWfBeLRqFOgVjIc0r\nbSfQGW+5IEn1g4bHRTdTIWyqw9spTsELjZV0ais5AoGACxOzRy+pkndYtoM2hJRk\nRhAER5a6YwW6cz/y0vJRNY9buubPFFpLXf2U3LkqPyZHa5F7W0VRkXtykxf4/Ast\nmxur3CmfjAoxUDGptif1alLTxqW868kzO5IWKAVWzasIjoKK+klmvC/IW6wyzm5b\nn8Krv09LUZ180wC9nQ4dg1w=\n-----END PRIVATE KEY-----\n",
        "client_email": os.getenv("client_email"),#"firebase-adminsdk-o4xed@betquty-capital.iam.gserviceaccount.com",
        "client_id": os.getenv("client_id"),#"104467937332716564053",
        "auth_uri": os.getenv("auth_uri"),# "https://accounts.google.com/o/oauth2/auth",
        "token_uri": os.getenv("token_uri"),# "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": os.getenv("auth_provider_x509_cert_url"), #"https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("client_x509_cert_url"), #"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-o4xed%40betquty-capital.iam.gserviceaccount.com"
    });
    default_app = firebase_admin.initialize_app(cred_obj, {
        'databaseURL': 'https://betquty-capital-default-rtdb.firebaseio.com/'
    })

def getTodayInDBFormat():
    return datetime.today().strftime('%Y-%m-%d')

def get_DK_spreads():
    ''' PULLS THE DK SPREADS AND RETURNS A DICTIONARY WITH THE MATCHUPS AND SPREADS '''
    api = 'https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey='+key+'&regions=us&markets=spreads&oddsFormat=american&bookmakers=draftkings'
    response_API = requests.get(api)
    data = response_API.text
    parse_json = json.loads(data)
    matchups = []

    for item in parse_json:
        home = item["home_team"]
        away = item["away_team"]
        try:
            x = item["bookmakers"][0]["markets"][0]["outcomes"]
            for team in x:
                if team["name"] == home:
                    home_spread = team["point"]
                elif team["name"] == away:
                    away_spread = team["point"]
                else:
                    print("Could not find one of the teams in DK")
            matchup = {}
            matchup['game'] = home + " vs " + away
            matchup['DK_home_name'] = home
            matchup['DK_away_name'] = away
            matchup['DK_home_spread'] = home_spread
            matchup['DK_away_spread'] = away_spread
            matchups.append(matchup)
        except Exception as e:
            print(home_spread)
            print(away_spread)
            print(matchup)
            print(item)
            print("ERROR: " + home + " vs. " + away + " \n")
            print(e)
            print("\n\n\n\n")
            continue

    return matchups



def set_matchup(team1, team2): # these teams should be part of the Team class already
    X = []
    try:
        team_data = pd.read_csv("output/{}_teams.csv".format(str(season)))
        try:
            t1 = team_data.loc[team_data['Name'] == team1]
        except:
            print("Error loading " + team1)
        try:
            t2 = team_data.loc[team_data['Name'] == team2]
        except: 
            print("Error loading " + team2)
        t1 = t1.values.tolist()
        t2 = t2.values.tolist()
        t1 = t1[0]
        t2 = t2[0]

        t1.pop(0)
        t2.pop(0)
        Xinput = []

        for i,entry in enumerate(t1):
                if i == 1: # take the average of the teams' paces
                    num = (t1[i] + t2[i]) / 2
                    Xinput.append(num)
                else:
                    num = (t1[i] - t2[i]) / t1[i] # make each state relative to the other teams'; percent difference with (t1 - t2) / t1
                    Xinput.append(num)
                X.append( Xinput )
        return X

    except Exception as e:
        print("Error in set_matchup: " + str(e) + "\nTeams are " + home + " and " + away)
        pass

def run_model(X1, X2, model):
    try:
        spread1 = model.predict(X1)[0][0]
        spread2 = model.predict(X2)[0][0]
        print(spread1)
        spread = round(float(spread1),1)
        if (spread < 0):
            spread = "+" + str(0 - spread)
        elif (spread == 0):
            spread = str(spread)
        else:
            spread = "-" + str(spread)
    except Exception as e:
        print("Error in run_model: error is " + str(e))

    return(spread)

def games_today():
    games = get_DK_spreads()
    return (games)


def calc_spread(home, away, model):
    X1 = set_matchup(home, away)
    X2 = set_matchup(away, home)
    spread = (run_model(X1, X2, model))
    return spread


def print_spreads(games):
    ''' takes the DK matchups, converts name to sportsref name, pulls data, and runs model '''
    output = []
    for matchup in games:
        try:
            DK_home_name = matchup["DK_home_name"]
            DK_away_name = matchup["DK_away_name"]


            STATS_home_name = name_conversion[DK_home_name]
            STATS_away_name = name_conversion[DK_away_name]
        
            home_spread = calc_spread(STATS_home_name, STATS_away_name, model)
            temp = {}
            temp["home"] = STATS_home_name
            temp["away"] = STATS_away_name
            temp["DK_home"] = DK_home_name
            temp["DK_away"] = DK_away_name
            temp["model_home_spread"] = home_spread
            temp["model_away_spread"] = str(-(float(home_spread)))
            temp["DK_home_spread"] = matchup["DK_home_spread"]
            temp["DK_away_spread"] = matchup["DK_away_spread"]
            output.append(temp)
        except Exception as e:
            print('Error in the name conversion function: ' + str(e))
            continue
    return output

def csv_format(games):
    output = [["HomeTeam", "HomeSpread","AwayTeam","AwaySpread"]]
    for date in games:
        for game in games[date]:
            try:
                home = game["home_name"]
                away = game["away_name"]
                home_abbr = game["home_abbr"].upper()
                away_abbr = game["away_abbr"].upper()
                spread = calc_spread(home_abbr, away_abbr, model)
                if spread[0] == "+":
                    spread2="-" + spread[1:]
                else:
                    spread2= "+" + spread[1:]
                output.append([home_abbr,spread,away_abbr,spread2])
            except Exception as e:
                print("Exception in 'csv_format': " + str(e))
                continue
    return output

def calculatePick(matchup):
    model_home = float(matchup["model_home_spread"])
    dk_home = float(matchup["DK_home_spread"])
    model_away = float(matchup["model_away_spread"])
    dk_away = float(matchup["DK_away_spread"])
    home_diff = dk_home - model_home
    away_diff = dk_away - model_away

    calculation = {}

    if (home_diff > 0):
        calculation["home"] = True
        calculation["away"] = False
    if (away_diff > 0):
        calculation["home"] = False
        calculation["away"] = True
    if (home_diff == 0):
        calculation["home"] = False
        calculation["away"] = False
    print(calculation)
    return calculation
    
def comparison(matchups):
    output = []
    print(matchups)
    for matchup in matchups:
        try:
            pickObj = calculatePick(matchup)
            gameObj = {
                "home": {
                    "pick": pickObj["home"],
                    "prediction": float(matchup["model_home_spread"]),
                    "spread": float(matchup["DK_home_spread"]),
                    "code": matchup["home"],
                    "name": matchup["DK_home"]
                },
                "away": {
                    "pick": pickObj["away"],
                    "prediction": float(matchup["model_away_spread"]),
                    "spread": float(matchup["DK_away_spread"]),
                    "code": matchup["away"],
                    "name": matchup["DK_away"]
                }
            }

            output.append(gameObj)
            print("GameObj:")
            print(gameObj)
        except Exception as e:
            print("EXCEPTION")
            print(e)
            continue
    return output


def post_to_db(data):
    ref = db.reference('/' + getTodayInDBFormat())
    ref.set(output)

if __name__ == "__main__":
    #load_dotenv() # only use locally
    print("RUNNING PRIORITZED_BETS.PY")
    initFirebase()
    model = keras.models.load_model('spread_model')
    get_DK_spreads()
    games = games_today() # returns all games on inputted games

    output = print_spreads(games) # 
    output = comparison(output)
    post_to_db(output)
    print(output)

