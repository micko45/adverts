import requests
from bs4 import BeautifulSoup as bs
import datetime
import pandas as pd
import pickle
import mail_df

pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

allData = []
pk_file = "./files/data.pk"


def getAdsHTML(url):
    #some job sites are iffy when it comes to headers so spoof chrome
    headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Dnt": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    }

    r = requests.get(url, headers = headers)
    return r.content

def makeSoup(url):
    soup = bs(getAdsHTML(url), 'html.parser')
    return soup

def getAdsSoup(url):
    soup = makeSoup(url)
    adRows= soup.find_all('div', {'class': 'search_result info-box quick-peek-container'})
    return adRows

def getTitle(_input):
    title = _input.find_all('a')
    title = title[1].get_text().strip()
    return title 

def getPrice(_input):
    tmp = _input.find('div', {'class':'holder header'})
    price = tmp.find('dd').get_text().strip()
    return price

def getArea(_input):
    area = _input.find_all('a')
    area = area[3].get_text()
    return area

def getCounty(_input):
    county = _input.find_all('a')
    return county[4].get_text()

def getTodaysDate():
    return datetime.datetime.now().strftime("%d/%m/%Y")

def getID(_input):
    toReturn = _input.find('button', {'class':'quick-peek-btn'})
    toReturn = str(toReturn).split(" ")[2]
    toReturn = toReturn.split("\"")[1]

    return toReturn

def getCats(url):
    urlData = url.split("/")
    mainCat = urlData[4]
    subCat1 =  urlData[5]

    return mainCat, subCat1

def getProductURL(_input):
    adsURL = "https://www.adverts.ie"
    anchor = _input.find('a').get('href')
    anchor = adsURL + anchor
    return anchor

def getLastUpdate(_input, newMethod=False):
    tmp = _input.find('ul', {'class': 'date-entered'})
    lastUpdated = tmp.find_all('li')[2].get_text().strip()
  
    lastUpdatedDays = cleanLastUpdated(lastUpdated)
    return lastUpdated, lastUpdatedDays

def getComments(_input, newMethod=False):
  dateEnteredSection = _input.find('ul', {'class': 'date-entered'}) #Comments are in here
  _tmp = dateEnteredSection.find_all('li') # comments are in the 4th <li>
  if len(_tmp) > 3:
    numOfComments = _tmp[3].get_text().strip().replace(' comments', '').replace(' comment', '')
    return numOfComments
  else:
    return "0"
  #print(tmp.find_all('li')[3].get_text().strip())

def cleanLastUpdated(_input):
    if _input == "about a day ago":
        return 1
    elif _input == "1 day ago":
        return 1
    elif _input == "1 week ago":
        return 7
    elif _input == "1 month ago":
        return 30
    elif _input == "1 year ago":
        return 365
    elif "days" in _input:
        return cleanDays(_input)
    elif "weeks" in _input:
        return cleanWeeks(_input)
    elif "months" in _input:
        return cleanMonths(_input)
    elif "years" in _input:
        return cleanYears(_input)
    else: return 0

def cleanDays(days):
    return int(days.split(" ")[0])

def cleanWeeks(weeks):
    _tmp = weeks.split(" ")
    return int(_tmp[0]) * 7

def cleanMonths(months):
    _tmp = months.split(" ")
    return int(_tmp[0]) * 30

def cleanYears(years):
    _tmp = years.split(" ")
    return int(_tmp[0]) * 365

def breakOutData(_input, url):
    title = getTitle(_input)
    price = getPrice(_input)
    area = getArea(_input)
    county = getCounty(_input)
    id = getID(_input)
    mainCat, subCat = getCats(url)
    productURL = getProductURL(_input)
    lastUpdate, lastUpdateDays = getLastUpdate(_input)
    comments = getComments(_input)
    return [ title, price, area, county, id, mainCat, subCat, lastUpdate, productURL, lastUpdateDays, comments]

def createDataList(url):
    adRows = getAdsSoup(url)
    for i in adRows:
        returnedData = breakOutData(i, url)
        allData.append(returnedData)
    return allData

def quitProgram(message):
    print(message)
    exit()

def checkURL(urls):
    if type(urls) is not list:
        quitProgram(urls + " Is not a list of valid HTML links for advers.ie")
    else:
        return True

def pickleDump(df):
     pickle.dump(df, open(pk_file, 'wb'))

def makeDataFrame(urls):
    sendMail = False
    checkURL(urls)
    for url in urls:
        createDataList(url)
    df = pd.DataFrame(allData, columns = ['Title', 'Price', 'Area', 'County', 'ID', 'MainCat', 'SubCat', 'LastUpdate', 'Prod_URL', 'LastUpdateInDays', 'Comments'])
    df.drop_duplicates(inplace=True)
    df = df.sort_values(by = 'LastUpdateInDays')
    df['Prod_URL'] = '<a href=' + df['Prod_URL'] + '><div>' + 'url' + '</div></a>' # make the url a anchor
    pickleDump(df.drop([ 'LastUpdateInDays' ], axis=1))
    if sendMail == True:
      mail_df.sendDFAsMail(df.drop([ 'LastUpdateInDays' ], axis=1))
    else:
      df_tmp = df.drop([ 'LastUpdateInDays' ], axis=1)
      print(df_tmp.to_html(escape = False))
      df
    #printDF(df)

def printDF(df):
    pd.set_option('display.max_colwidth', 70)
    print(df.drop(['Prod_URL', 'LastUpdateInDays', 'MainCat', 'SubCat', 'ID'], axis=1))



if __name__ == "__main__":

    urls = [
        'https://www.adverts.ie/for-sale/computers/desktops/492/q_intel+nuc/private_seller/list_view',
         'https://www.adverts.ie/for-sale/electronics/other-electronics/50/q_bearcat/private_seller/list_view',
         'https://www.adverts.ie/for-sale/electronics/other-electronics/50/q_uniden/private_seller/list_view',
         'https://www.adverts.ie/for-sale/electronics/other-electronics/50/q_scanner+radio/private_seller/list_view',
         'https://www.adverts.ie/for-sale/electronics/other-electronics/50/q_shortwave/private_seller/list_view',
         'https://www.adverts.ie/for-sale/electronics/other-electronics/50/q_ham+radio/private_seller/list_view'
         ]


    makeDataFrame(urls)

