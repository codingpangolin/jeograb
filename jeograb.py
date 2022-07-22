# -*- coding: utf-8 -*-
"""
Created on Sat Jan 25 22:00:07 2020

@author: Alistair
"""
import bs4,time, requests, os
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class jeoGrab():
    def __init__(self,episodeno=None):
        if episodeno == None:
            self.html = self.dl_html()
        else:
            self.html = self.dl_episode(episodeno)
        self.soup = bs4.BeautifulSoup(self.html,'lxml')
        self.game_obj = {}
        self.lst_gametxt = []
        self.cashobj = {'jeopardy_round':{1:'$200',2:'$400',3:'$600',4:'$800',5:'$1000'},\
                  'double_jeopardy_round':{1:'$400',2:'$800',3:'$1200',4:'$1600',5:'$2000'}}

    def dl_html(self):
        mainpage = requests.get('http://www.j-archive.com/')
        mainsoup = bs4.BeautifulSoup(mainpage.text,'lxml')
        endurl = mainsoup.find(class_='splash_clue_footer').a['href']
        gamepage = requests.get('http://www.j-archive.com/'+endurl)

        return gamepage.text
    
    def dl_episode(self,episodeno):
        url = 'http://www.j-archive.com/showgame.php?game_id=' + str(episodeno)
        gamepage = requests.get(url)

        return gamepage.text
    
    def scrape_clues(self, roundname):
        fround = self.soup.find("div", {"id": roundname})
        
        quiz_dict = {}
            
        catresults = fround.find_all(class_='category_name')
        
        initcatno = 1
        for cat in catresults:
            quiz_dict[initcatno] = {'category_name':cat.text,'questions':{}}
            initcatno += 1
            
        clueresults = fround.find_all(class_='clue')
        
        for clue in clueresults:
            cluetext = clue.find(class_="clue_text")
            if cluetext != None:
                answerhtml = clue.div['onmouseover']
                clue_answer = bs4.BeautifulSoup(answerhtml,'lxml')
                answertxt = clue_answer.find(class_="correct_response").text
                cluetxt = cluetext.text
                cluetxtid = cluetext['id']
                catno = cluetxtid.split("_")[2]
                cluecatno = cluetxtid.split("_")[3]
        
                quiz_dict[int(catno)]['questions'].update([(int(cluecatno),\
                         {'cluetext':cluetxt,'answer':answertxt})])
        
        self.game_obj[roundname] = quiz_dict
        
    def scrape_final(self):
        fround = self.soup.find("div", {"id": "final_jeopardy_round"})
        catname = fround.find(class_='category_name').text
        clue = fround.find(class_="clue_text").text
    
        mousesoup = fround.div['onmouseover']
        mousesoupaltered = mousesoup.replace(r'\"',r'"')
        correct = bs4.BeautifulSoup(mousesoupaltered,'lxml').find(class_="correct_response").text
        
        self.game_obj['final'] = {'catname':catname,'cluetext':clue,'answer':correct}
        
    def game_details(self):
        details_str = self.soup.find("div", {"id": "game_title"}).text
        details_arr = details_str.split(' - ')
        show_arr = details_arr[0].split(' ')
    
        self.game_obj['details'] = {'date':details_arr[1],'show':show_arr[1]}
    
    def write_tsv(self):
        self.lst_gametxt.append(['Category', 'Cash','Clue','Answer'])

        for rname in ['jeopardy_round','double_jeopardy_round']:
            for catno in range(1,7):
                for clueno in range(1,6):
                    if clueno in self.game_obj[rname][catno]['questions']:
                        catname = self.game_obj[rname][catno]['category_name']
                        catarr = self.game_obj[rname][catno]['questions'][clueno]
                        cash = self.cashobj[rname][clueno]
                        self.lst_gametxt.append([catname,cash,catarr['cluetext'],\
                                               catarr['answer']])
        finaljeop = self.game_obj['final']
        self.lst_gametxt.append([finaljeop['catname'],'N/A',finaljeop['cluetext'],\
                               finaljeop['answer']])

    def gen_quiz(self):
        show = self.game_obj['details']['show']
        showdate = self.game_obj['details']['date']

        url = 'https://www.jetpunk.com/create-quiz'
        
        options = webdriver.ChromeOptions()
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument('--headless')
        options.add_argument('--window-size=1300,1000')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=options)
        driver.get(url)
        print('retrieving data')
        driver.find_element_by_class_name('login-link').click()
        time.sleep(5)
        driver.find_element_by_class_name('txt-email').send_keys(os.environ.get("JETPUNK_USER"))
        driver.find_element_by_class_name('txt-password').send_keys(os.environ.get("JETPUNK_PW"))
        driver.find_element_by_class_name('login-button').click()
        time.sleep(10)
        driver.find_element_by_class_name('green').click()
        time.sleep(5)
        driver.find_element_by_name('title').clear()
        driver.find_element_by_name('title').send_keys('Jeopardy ' + show)
        driver.find_element_by_name('instructions').clear()
        driver.find_element_by_name('instructions').send_keys('Episode broadcast ' + showdate)
        driver.find_element_by_name('seconds').send_keys(Keys.CONTROL, 'a')
        driver.find_element_by_name('seconds').send_keys(Keys.BACKSPACE)
        driver.find_element_by_name('seconds').send_keys('8:00')
        driver.find_element_by_xpath('//*[@title="Step 2"]').click()
        time.sleep(5)
        driver.find_element_by_id('answers-advanced').click()
        time.sleep(5)
        xpathstring = '/html/body/div/div/div[2]/div[3]/div/div/div/div/div[1]/div[1]/div[2]/div[6]/table/tbody/tr[{}]/td[{}]/div'
        driver.find_element_by_xpath(xpathstring.format(2,2)).click()

        driver.find_element_by_id('btn-add-del-acols').click()
        driver.find_element_by_id('btn-add-del-acols').click()

        numrows_to_add = len(self.lst_gametxt) - 16
        for numrows in range(1,numrows_to_add+1):
            driver.find_element_by_id('btn-add-del-answers').click()
        ansrowno = 1
        for answer_lst in self.lst_gametxt:
            if ansrowno == 1:
                anscol = 1
            else:
                anscol = 2
            for datum in answer_lst:
                driver.find_element_by_xpath(xpathstring.format(ansrowno,anscol)).click()
                driver.find_element_by_xpath(xpathstring.format(ansrowno,anscol)).clear()
                driver.find_element_by_xpath(xpathstring.format(ansrowno,anscol)).send_keys(datum)
                print(datum)
                anscol += 1
            ansrowno += 1

        time.sleep(10)
        driver.find_element_by_xpath('//*[@title="Step 4"]').click()
        selectbox = Select(driver.find_element_by_id('sel-design-mode'))
        for opt in selectbox.options:
            selectbox.select_by_visible_text('Manual')
        driver.find_element_by_id('design-advanced').click()
        driver.find_element_by_id('btn-format-groups-of-things').click()
        selectbox = Select(driver.find_element_by_id('sel-groupify-blocks'))
        for opt in selectbox.options:
            selectbox.select_by_visible_text('1')
        driver.find_element_by_id('btn-confirm-format-groups').click()
        time.sleep(10)
        driver.find_element_by_class_name('close').click()
        driver.find_element_by_id('btn-save').click()
        time.sleep(10)
        driver.find_element_by_class_name('close').click()
        time.sleep(10)
        print('Submitting quiz')
        driver.find_element_by_xpath('//*[@title="Step 5"]').click()
        time.sleep(10)
        driver.find_element_by_id('btn-submit-quiz').click()
        time.sleep(10)
        driver.quit()
        
    def scrape_game(self):
        self.scrape_clues('jeopardy_round')
        self.scrape_clues('double_jeopardy_round')
        self.game_details()
        self.scrape_final()

    def execute(self):
        print('about to scrape game')
        self.scrape_game()
        print('about to create data file')
        self.write_tsv()
        print('about to generate quiz')
        self.gen_quiz()
