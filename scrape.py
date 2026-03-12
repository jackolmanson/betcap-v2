from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd


# URL to scrape
year = '2026'
url = 'https://www.sports-reference.com/cbb/seasons/' + year + '-advanced-school-stats.html'
url2 = 'https://www.sports-reference.com/cbb/seasons/' + year + '-advanced-opponent-stats.html'

# collect HTML data
html = urlopen(url)
html2 = urlopen(url2)

# create soup object
soup = BeautifulSoup(html, features='lxml')
soup2 = BeautifulSoup(html2, features='lxml')

# use getText() to extract headers into list
headers = [th.getText() for th in soup.findAll('tr', limit=2)[1].findAll('th')]
headers.pop(0)
#print(headers)

x = 1
for i in range(len(headers)):
    if len(headers[i]) < 2:
        print(x)
        headers[i] = x
        x = x+1


# get rows from table
rows = soup.findAll('tr')[2:]
rows_data = [[td.getText() for td in rows[i].findAll('td')]
        for i in range(len(rows))]

#print(rows_data[0])

# do the same to get opp shooting % 
# use getText() to extract headers into list
headers2 = [th.getText() for th in soup2.findAll('tr', limit=2)[1].findAll('th')]
headers2.pop(0)
headers.append('OpTS%')

# get rows from table
rows2 = soup2.findAll('tr')[2:]
rows_data2 = [[td.getText() for td in rows2[i].findAll('td')]
        for i in range(len(rows2))]


for n in range(0,len(rows_data)):
    try:
        # add opp true shooting %
        rows_data[n].append(rows_data2[n][24])
        # data processing
        rows_data[n][0] = rows_data[n][0].upper()
        rows_data[n][0] = rows_data[n][0].replace(' ','-')
        rows_data[n][0] = rows_data[n][0].replace('&',"")
        rows_data[n][0] = rows_data[n][0].replace('.',"")
        rows_data[n][0] = rows_data[n][0].replace('(',"")
        rows_data[n][0] = rows_data[n][0].replace(')',"")
        rows_data[n][0] = rows_data[n][0].replace("'","")
    except:
        continue

rows_data = list(filter(None, rows_data))


# create the dataframe
df = pd.DataFrame(rows_data, columns = headers)

# remove unneeded columns
for x in range(1,15):
    del df[x]
del df["W-L%"]
del df['SRS']
del df['SOS']
del df['BLK%']
del df['ORB%']
del df['FT/FGA']
del df['Tm.']
del df['Opp.']
del df['eFG%']
del df['FTr']
del df['3PAr']
del df['AST%']

df.columns = ["Name", "Pace", "OffensiveRating", "TrueShooting%","TotalRebound%","Steal%","Turnover%","OppTrueShooting%"]
print(df)


df2 = df.iloc[:,[0,2,1,5,3,6,4,7]]
print(df2)
df.to_csv('./output/{}_teams.csv'.format(year),index=None)

