import bs4 as bs
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    def __init__(self, outputCatalog = None, use_proxy=True, debug=True):

        self.TIMESLEEP = 5 #sec
        self.ATTEMPT_UPDATE = 5 # count
        self.urlList = ["https://spb.hh.ru/vacancies/programmist"]
        self.proxy_list = ["217.79.3.94:8080","83.171.96.249:8080","78.107.254.213:8080"];
        self.ignoreList = ["Россия"]
        self.url = self.urlList[0]

        self.statistics = {"passed":int(0),"successful":int(0),"pages":int(0), "regions":int(0)}
        self.regions = list()
        self.last_region = 0
        self.page = 0
        self.information = list()

        if( outputCatalog == None):
            raise Exception("Output catalog should been is set")

        self.outputCatalog = outputCatalog

        postfix = str(datetime.datetime.now().time()).split(":")[0:2]
        postfix = "_"+"_".join(postfix)

        if(not os.path.exists(self.outputCatalog)):
            os.makedirs(self.outputCatalog)
        else:
            os.rename(self.outputCatalog,self.outputCatalog+postfix)
            os.makedirs(self.outputCatalog)

        self.createLoger()

        options = webdriver.ChromeOptions()
        if (not debug):
            options.add_argument('headless')

        if(use_proxy):
            self.proxy = self.proxy_list[0];
            options.add_argument('--proxy-server=http://%s' % self.proxy)
        else:
            self.proxy = None

        self.engine = webdriver.Chrome(options=options)

        self.logger.info("Start HeadHunterScraper module")
        self.resetPage()

        pass

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

            logging.warning("Next page --> Current page: {} max page: {}".format(str(current_page),str(max_page)))

            if((current_page < max_page) and max_page != None and current_page != None):

                logging.warning("Update page. Caller nextPage()")
                time.sleep(self.TIMESLEEP)
                self.engine.refresh()

                experience = k + 1

                if experience < self.ATTEMPT_UPDATE:
                    logging.info("I can`t switch to next page. Attempt:{}. Current page:{} Max page: {} ".format(str(experience),str(current_page),str(max_page)))
                    return self.nextPage(experience)
                else:
                    logging.error("I can`t switch to next page. Count of attempt bigger {}.  Current page: {} Max page: {}.".format(str(self.ATTEMPT_UPDATE),str(current_page),str(max_page)))
                    raise Exception("I can`t switch to next page")
            else:
                logging.error("I can`t switch to next page.  Current page: {} Max page: {}.".format(str(current_page),str(max_page)))
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
                logging.error("I can`t update vacancy list")
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
            logging.warning("I can`t update regions. Attempt: #"+str(attempt))

            if ( attempt < self.ATTEMPT_UPDATE):
                return self.updateRegion(attempt)
            else:
                logging.error("I can`t update regions. Break")
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

        return self.engine.find_element_by_class_name("sticky-container"). \
            find_element_by_class_name('clusters-group__items')
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
            logging.info("I try update region !")
            return self.updateRegion()
        except:
            logging.warning("I can`t update region !")
            attempt = k + 1

            if(attempt < self.ATTEMPT_UPDATE):
                logging.warning("I can`t switch to next region. Sleep: {} sec".format(str(self.TIMESLEEP)))
                time.sleep(self.TIMESLEEP)
                self.engine.refresh()
                logging.warning("Refresh page.")
                return self.globalUpdateRegion(attempt)
            else:
                logging.error("I can`t switch to next region. Global error ")
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
            if region == ignore:
                return True
        return  False

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


    def getVacancy(self):

        self.regions = self.updateRegion()

        for i in range(len(self.regions)):

            catalogRegion = os.path.join(self.outputCatalog,str(i))
            self.last_region = i

            if( not os.path.exists(catalogRegion)):
                os.makedirs(catalogRegion)

            if(self.checkIgnore(self.regions[i].text)):
                continue

            self.regions[i].click()

            self.page = 1

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
                            logging.error("I can`t update this page #"+ str(self.page))

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
                        pageName =str("page")+str(self.statistics["pages"])+str(".pickle")
                        self.save(name=pageName)
                        self.page += 1
                        self.nextPage()
                    except:
                        logging.error("I can`t switch to next page. Find vacancy:{} Processed page: {}. Region: {}".format(str(findVacancy),str(self.page),str(self.last_region)))
                        break
            except:
                logging.error("I can`t process this page")

            try:
                self.globalUpdateRegion()
                self.statistics["regions"] += 1
            except:
                self.logger.error("Global exception ! I can`t work in this region")
                continue

        pass