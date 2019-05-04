import bs4 as bs
import pandas as pd
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import subprocess
import pickle
import os
from geopy.geocoders import Nominatim
from geopy.geocoders import Yandex

import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
import logging
import argparse
from glob2 import glob
import datetime
import threading


class HeadHunterScraper(object):
    def __init__(self, outputCatalog = None, use_proxy=True, headless = False, debug=False):

        self.TIMESLEEP = 1 #sec
        self.ATTEMPT_UPDATE = 5 # count
        self.urlList = ["https://spb.hh.ru/vacancies/programmist"]
        self.ignoreList = ["Россия"]
        self.url = self.urlList[0]
        self.engine = None

        self.statistics = {"passed":int(0),"successful":int(0),"pages":int(0), "regions":int(0)}
        self.regions = list()
        self.last_region = 0
        self.page = 0
        self.information = list()

        if( outputCatalog == None):
            raise Exception("Output catalog should been is set")

        self.outputCatalog = outputCatalog

        # postfix = str(datetime.datetime.now().time()).split(":")[0:2]
        # postfix = "_"+"_".join(postfix)

        if(not os.path.exists(self.outputCatalog)):
            os.makedirs(self.outputCatalog)
        # else:
        #     os.rename(self.outputCatalog,self.outputCatalog+postfix)
        #     os.makedirs(self.outputCatalog)

        self.createLoger()

        self.proxy = None

        self.makeEngine(headless=headless)

        self.logger.info("Start  HeadHunter module !!!")
        pass

    def removeEngine(self):
        self.engine.quit()
        pass

    def makeEngine(self,headless=False,use_proxy =True):

        try:
            if(self.engine != None):
                self.removeEngine()

            self.options = webdriver.ChromeOptions()

            if headless:
                self.options.add_argument('--headless')

            # if(use_proxy):
                # self.proxy = self.upadteProxy()
                # self.options.add_argument('--proxy-server=http://%s' % self.proxy)

            self.engine = webdriver.Chrome(options=self.options)

            # # options = webdriver.FirefoxOptions()
            # # options.headless = True
            #
            # binary = FirefoxBinary(r"C:\tools\tor\Tor Browser\Browser\firefox.exe")
            # profile = FirefoxProfile(r"C:\tools\tor\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default")
            #
            # self.engine = webdriver.Firefox(firefox_binary=binary,firefox_profile=profile)

            self.logger.info("Make engine")
            self.resetPage()

        except:
            time.sleep(10)
            self.makeEngine()

        pass

    def upadteProxy(self):

        try:
            page = requests.get("https://www.sslproxies.org/")
            soup = bs.BeautifulSoup(page.content,"html.parser")

            sslProxyTable = soup.find('tbody')


            for row in sslProxyTable.findAll("tr"):

                addressInfo = row.findAll("td")

                if(str(addressInfo[4]).find("anonymous") == -1):
                    continue
                proxy = addressInfo[0].text +":"+addressInfo[1].text

                def checkIp(ip):
                    response = subprocess.run(["ping","-n","1",ip]).returncode
                    return  True if response == 0 else False;

                if(checkIp(addressInfo[0])):
                    break

        except:
            return proxy
            # proxy = self.upadtePll = proxy()

        return proxy

    def resetPage(self):
        if self.engine == None:
            raise Exception("I can`t find engine")

        self.logger.info("Reset page:{}. Use proxy:{}".format(self.url,self.proxy))
        self.engine.get(self.url)
        pass

    def defaultPage(self):
        if self.engine == None:
            raise Exception("I can`t find engine")
        try:
            self.getListFromRegions().click()
        except:
            time.sleep(self.TIMESLEEP)
            self.getListFromRegions().click()

        try:
            self.getListFromRegions().find_elements_by_tag_name("a")[0].click()
        except:
            time.sleep(self.TIMESLEEP)
            self.getListFromRegions().find_elements_by_tag_name("a")[0].click()
        pass

    def nextPage(self, k=0):

        if self.engine == None:
            raise Exception("I can`t find engine")

        try:
            buttonContinue = self.engine.find_element_by_class_name("sticky-container"). \
                find_element_by_css_selector("a.bloko-button.HH-Pager-Controls-Next.HH-Pager-Control")
            link = buttonContinue.get_attribute("href")
            self.engine.get(link)
        except:

            try:
                current_page = self.engine.find_elements_by_css_selector("span.bloko-button.bloko-button_pressed").text
                current_page = int(current_page)
            except:
                current_page = None

            try:
                controls = self.engine.find_elements_by_css_selector("a.bloko-button.HH-Pager-Control")

                if(str(controls[-1].text).find('дальше') >= 0):
                    max_page = int(controls[-2].text)
                else:
                    max_page = int(controls[-1].text)
            except:
                max_page = None

            self.logger.warning("Next page --> Current page: {} max page: {}".format(str(current_page),str(max_page)))

            if((current_page < max_page) and max_page != None and current_page != None):

                self.logger.warning("Update page. Caller nextPage()")
                time.sleep(self.TIMESLEEP)
                self.engine.refresh()

                experience = k + 1

                if experience < self.ATTEMPT_UPDATE:
                    self.logger.info("I can`t switch to next page. Attempt:{}. Current page:{} Max page: {} ".format(str(experience),str(current_page),str(max_page)))
                    return self.nextPage(experience)
                else:
                    self.logger.error("I can`t switch to next page. Count of attempt bigger {}.  Current page: {} Max page: {}.".format(str(self.ATTEMPT_UPDATE),str(current_page),str(max_page)))
                    raise Exception("I can`t switch to next page")
            else:
                self.logger.error("I can`t switch to next page.  Current page: {} Max page: {}.".format(str(current_page),str(max_page)))
                raise Exception("I can`t switch to next page")
        pass

    def updateVacancy(self,k=0):
        try:
            vacancyBlock = self.engine.find_element_by_class_name("sticky-container")
            vacancy = vacancyBlock.find_elements_by_css_selector('div.vacancy-serp-item.vacancy-serp-item_premium')
            vacancy += vacancyBlock.find_elements_by_css_selector("div.vacancy-serp-item")
        except:
            time.sleep(self.TIMESLEEP)
            experience = k + 1
            if experience < 10:
                return self.updateVacancy(experience)
            else:
                self.logger.error("I can`t update vacancy list")
                raise Exception("I can`t update vacancy list")
        return vacancy

    def updateRegion(self,k=0):
        if self.engine == None:
            raise Exception("I can`t find engine")

        try:
            self.resetPage()
            self.defaultPage()
            self.getMoreRegion().click()
            self.regions = self.getFullRegions().find_elements_by_tag_name("a")

        except:
            attempt = k + 1
            time.sleep(self.TIMESLEEP * 10)

            self.logger.warning("I can`t update regions. Attempt: #"+str(attempt))

            if ( attempt < self.ATTEMPT_UPDATE):
                return self.updateRegion(attempt)
            else:
                self.logger.error("I can`t update regions. Break")
                raise Exception("I can`t update regions. Break")

        return self.regions

    def getListFromRegions(self):

        if self.engine == None:
            raise Exception("I can`t find engine")

        return  self.engine.find_element_by_class_name("sticky-container") \
            .find_element_by_class_name("clusters-list__item")
        pass

    def getMoreRegion(self):

        if self.engine == None:
            raise Exception("I can`t find engine")

        return self.engine.find_element_by_class_name("sticky-container"). \
            find_element_by_class_name('clusters-group__items'). \
            find_element_by_class_name("clusters-list__item_more")

        pass

    def getFullRegions(self):
        if self.engine == None:
            raise Exception("I can`t find engine")

        return self.engine.find_element_by_css_selector("div.sticky-container")\
                   .find_element_by_css_selector('div.clusters')\
                   .find_elements_by_css_selector("div.clusters-group.clusters-group_expand")[0]

        # return self.engine.find_element_by_class_name("sticky-container"). \
        #     find_element_by_class_name('clusters-group__items')
        pass

    # def checkIgnore(self):
    #
    #     for ignore in self.ignoreList:
    #         if region == ignore:
    #             return True
    #
    #     return  False
        pass

    def globalUpdateRegion(self,k=0):
        if self.engine == None:
            raise Exception("I can`t find engine")

        try:
            self.logger.info("I try update region !")
            return self.updateRegion()
        except:
            self.logger.warning("I can`t update region !")
            attempt = k + 1

            if(attempt < self.ATTEMPT_UPDATE):
                self.logger.warning("I can`t switch to next region. Sleep: {} sec".format(str(self.TIMESLEEP)))
                time.sleep(self.TIMESLEEP)
                self.engine.refresh()
                self.logger.warning("Refresh page.")
                return self.globalUpdateRegion(attempt)
            else:
                self.logger.error("I can`t switch to next region. Global error ")
                raise Exception("I can`t switch to next region. Global error ")
        pass

    def createLoger(self):

        id  = threading.current_thread().ident
        name = str("HeadHunter") +"_"+str(id)
        self.logger = logging.getLogger(name);
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(os.path.join(self.outputCatalog,name + ".log"))

        formatter = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(formatter)

        self.logger.addHandler(fh);

        pass

    def debug_msg(self,msg):
        self.logger.debug(msg)
        pass

    def save(self, name = "HeadHunter.pickle"):

        if name == None:
            self.logger.error("I can`t save file, becose name is None")
            raise Exception("Save file is failed")

        pathToFile = os.path.join(self.outputCatalog,str(self.last_region),name);

        with open(pathToFile,"wb") as f:
            pickle.dump(self.information,f)
            self.logger.info(str("Write information in pickle file. Region: {}. Page: {} . Find: {} vacancy.".format(str(self.last_region),str(self.page),str(len(self.information)))))
        pass

    def checkIgnore(self,region):

        for ignore in self.ignoreList:
            if str(region).find(ignore) >= 0:
                return True
        return  False

    def checkMetro(self):

        try:
            metrocss = self.engine.find_element_by_css_selector("div.sticky-container") \
                    .find_element_by_css_selector('div.clusters') \
                    .find_elements_by_css_selector("div.clusters-group.clusters-group_expand")[2]


            metro = metrocss.find_element_by_css_selector("div.clusters-group-title.clusters-group-title_selectable").text

            if str(metro).find("Метро") != -1 :
                result = True
            else:
                result =False
        except:
            result = False

        return result

    def getListMetroStations(self):

        try:

            metrocss = self.engine.find_element_by_css_selector("div.sticky-container") \
                .find_element_by_css_selector('div.clusters') \
                .find_elements_by_css_selector("div.clusters-group.clusters-group_expand")[2]

            result = metrocss.find_elements_by_css_selector("a.clusters-value")
        except:
            result = None

        return result

    def getCity(self, vacancy):

        try:
            city = vacancy.find_element_by_css_selector("span.vacancy-serp-item__meta-info").text
        except:
            self.statistics["passed"] += 1
            city = None

        return city

    def getLanguage(self,vacancy):
        try:
            language = vacancy.find_element_by_css_selector("div.resume-search-item__name").text
        except:
            language = "UNKNOWN"

        return language

    def getSalary(self, vacancy):

        try:
            salary =vacancy.find_element_by_css_selector("div.vacancy-serp-item__compensation").text
        except:
            salary = str(0)

        return salary

    def getTools(self, vacancy):

        tools = list()
        try:
            a=vacancy.find_element_by_css_selector("div.resume-search-item__name").find_element_by_tag_name("a")
            href = a.get_attribute("href")
            self.engine.get(href)

            #proccess
            skills = self.engine.find_elements_by_css_selector("span.Bloko-TagList-Text")

            for skill in skills:
                tools.append(skill.text)

            self.engine.back()
        except:
            tools.append("empty")
            errText = "I can`t get info about skills. Page: "+str(self.page)
            self.logger.error(errText)

        return tools

    def getLocation(self,city, geolocator = Yandex()):

        try:
            # geolocator = Yandex();
            gcode = geolocator.geocode(city)
            latitude  = gcode.latitude
            longitude = gcode.longitude
        except:
            latitude = float(0)
            longitude = float(0)

        return latitude, longitude

    def scraping(self):

        # Proccess
        try:
            findVacancy = int(0)
            while True:

                try:
                    vacancy = self.updateVacancy()
                except:
                    self.logger.error("I can`t update this page #"+ str(self.page))

                self.information = list()

                for j in range(len(vacancy)):

                    tools = list()

                    try:
                        vacancy = self.updateVacancy()
                    except:
                        self.logger.error("I can`t update this page #"+ str(self.page))

                    try:
                        city = self.getCity(vacancy[j])
                        salary = self.getSalary(vacancy[j])
                        tools = self.getTools(vacancy[j])
                        language = self.getLanguage(vacancy[j])
                        latitude,longitude = self.getLocation(city=city)

                        if city != None:
                            self.information.append({"city":str(city),"language":str(language), "salary":str(salary), "tools":tools, "latitude":latitude,"longitude":longitude})
                            self.statistics["successful"] += 1
                            findVacancy += 1

                    except:
                        self.logger.warning("passed: " + str(city)+" " + str(language) + " " + str(salary)+" "+str(tools))
                        self.statistics["passed"] += 1
                        continue

                try:

                    self.statistics["pages"] += 1
                    pageName =str("page_")+str(self.page)+str(".pickle")
                    self.save(name=pageName)
                    self.page += 1
                    self.nextPage()
                except:
                    self.logger.error("I can`t switch to next page. Find vacancy:{} Processed page: {}. Region: {}".format(str(findVacancy),str(self.page),str(self.last_region)))
                    break
        except:
            self.logger.error("I can`t process this page")
        pass

    def process(self, start=0):

        self.regions = self.updateRegion()

        for i in range(start,len(self.regions)):

            nameRegion = self.regions[i].text

            catalogRegion = os.path.join(self.outputCatalog,nameRegion)
            self.last_region = nameRegion

            if(self.checkIgnore(nameRegion)):
                continue

            if( not os.path.exists(catalogRegion)):
                os.makedirs(catalogRegion)


            self.regions[i].click()

            self.page = 1

            try:
                if self.checkMetro():

                    stations = self.getListMetroStations()

                    if(stations == None):
                        self.logger.error("I can`t find metro")
                        raise Exception("I can`t find metro")

                    for istation in range(len(stations)):
                        stations[istation].click()
                        self.scraping()
                        stations = self.getListMetroStations()
                        stations[0].click()
                        stations = self.getListMetroStations()

                        if(stations == None):
                            self.logger.error("I can`t find metro")
                            raise Exception("I can`t find metro")
                else:
                    # Proccess
                    self.scraping()
            except:
                self.logger.error("I can`t process region")

            try:
                self.globalUpdateRegion()
                self.statistics["regions"] += 1
            except:
                self.logger.error("Global exception ! I can`t work in this region")
                continue
        pass

    def append(self):

        catalogs = glob(os.path.join(self.outputCatalog,"**","*"),recursive=True)

        catalogs = [ str(os.path.split(x)[-1]).split(" ")[0] for x in catalogs if os.path.isdir(x) ]
        regions = [ str(region.text).split(" ")[0] for region in self.updateRegion() ]

        self.ignoreList += list(set(catalogs).intersection(set(regions)))
        self.ignoreList = sorted(self.ignoreList)

        self.process()

        pass



    def dump(self):

        file = os.path.join(self.outputCatalog,"hh.pickle")

        dumpFiles = glob(os.path.join(self.outputCatalog,"**","*.pickle"))

        allVacancys = list()

        for line in dumpFiles:
            with open(line,"rb") as f:
                allVacancys += pickle.load(f)

        with open(file,"wb") as f:
            pickle.dump(allVacancys,f)

        pass
