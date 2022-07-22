# -*- coding: utf-8 -*-
"""
Created on Fri May 29 23:15:53 2020

@author: Alistair
"""
import requests, bs4, time, jeograb, schedule
from datetime import datetime

def main_script():
    try:
        print('starting...')
        
        attemptno = 3
        
        while attemptno > 0:
            mainpage = requests.get('http://www.j-archive.com/')
            mainsoup = bs4.BeautifulSoup(mainpage.text,'lxml')
            endurl = mainsoup.find(class_='splash_clue_footer')
            if '#' in endurl.text:
                splitend = endurl.text.split(' ')
                broadcast_date = splitend[-1]
        
            if broadcast_date == datetime.today().strftime('%Y-%m-%d'):
                print(broadcast_date)
                print(datetime.today().strftime('%Y-%m-%d'))
                url_str = endurl.a['href']
                if '=' in url_str:
                    splitlink = url_str.split('=')
                    episodeid = splitlink[-1]
                    jeoobj = jeograb.jeoGrab(episodeid)
                    jeoobj.execute()
                break
            else:
                attemptno = attemptno - 1
                time.sleep(3600)
    except Exception as e:
        print(str(e))

schedule.every().monday.at('19:00').do(main_script)
schedule.every().tuesday.at('19:00').do(main_script)
schedule.every().wednesday.at('19:00').do(main_script)
schedule.every().thursday.at('19:00').do(main_script)
schedule.every().friday.at('19:00').do(main_script)

while True:
    schedule.run_pending()
    time.sleep(1)