import bs4 as bs
# from dalab import *
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
import pandas as pd

from headHunterScraper import HeadHunterScraper,DataHunter

ATTEMPT_UPDATE = int(5)
TIMESLEEP = int(1)
GLOBAL_SLEEP = int(360)

def getLocation(city):

    try:
        geolocator = Yandex();
        # geolocator = Nominatim();

        gcode = geolocator.geocode(city)
        latitude  = gcode.latitude
        longitude = gcode.longitude

        return latitude, longitude
    except:
        return float(0),float(0)

def getHHInfo(args):

    outputCatalog = args.out

    postfix = str(datetime.datetime.now().time()).split(":")[0:2]
    postfix = "_"+"_".join(postfix)

    if(not os.path.exists(outputCatalog)):
        os.makedirs(outputCatalog)
    else:
        os.rename(outputCatalog,outputCatalog+postfix)
        os.makedirs(outputCatalog)

    fileLogging = "HH" + postfix + ".log"
    fileLogging = os.path.join(outputCatalog,fileLogging)
    logging.basicConfig(filename=fileLogging,level=logging.INFO,filemode="w")

    statistics = {"passed":int(0),"successful":int(0),"pages":int(0), "regions":int(0)}
    ignoreList = ["Россия"]

    def resetPage(engine=None):
        if engine == None:
            raise Exception("I can`t find engine")

        url ="https://spb.hh.ru/vacancies/programmist"
        engine.get(url)
        time.sleep(TIMESLEEP)

    def getListFromRegions(engine = None):

        if engine == None:
            raise Exception("I can`t find engine")

        return  engine.find_element_by_class_name("sticky-container") \
            .find_element_by_class_name("clusters-list__item")

    def getMoreRegion(engine = None):
        if engine == None:
            raise Exception("I can`t find engine")

        return driver.find_element_by_class_name("sticky-container"). \
            find_element_by_class_name('clusters-group__items'). \
            find_element_by_class_name("clusters-list__item_more")

    def getFullRegions(engine = None):

        if engine == None:
            raise Exception("I can`t find engine")

        return driver.find_element_by_class_name("sticky-container").\
                      find_element_by_class_name('clusters-group__items')

    def defaultPage(engine=None):
        if engine == None:
            raise Exception("I can`t find engine")
        try:
            getListFromRegions(engine).click()
        except:
            time.sleep(TIMESLEEP)
            getListFromRegions(engine).click()

        try:
            getListFromRegions(engine).find_elements_by_tag_name("a")[0].click()
        except:
            time.sleep(TIMESLEEP)
            getListFromRegions(engine).find_elements_by_tag_name("a")[0].click()
        pass

    def checkIgnore(region):

        for ignore in ignoreList:
            if region == ignore:
                return True

        return  False

    def updateRegion(engine=None, k=0):
        if engine == None:
            raise Exception("I can`t find engine")

        try:
            resetPage(engine)
            defaultPage(engine)
            getMoreRegion(engine).click()
            regions = getFullRegions(engine).find_elements_by_tag_name("a")
        except:
            attempt = k + 1
            time.sleep(TIMESLEEP * 10)
            logging.warning("I can`t update regions. Attempt: #"+str(attempt))

            if ( attempt < ATTEMPT_UPDATE):
                return updateRegion(engine,attempt)
            else:
                logging.error("I can`t update regions. Break")
                raise Exception("I can`t update regions. Break")

        return regions

    def globalUpdateRegion(engine=None,k=0):
        if engine == None:
            raise Exception("I can`t find engine")

        try:
            logging.info("I try update region !")
            return updateRegion(engine)
        except:
            logging.warning("I can`t update region !")
            attempt = k + 1

            if(attempt < ATTEMPT_UPDATE):
                logging.warning("I can`t switch to next region. Sleep: {} sec".format(str(GLOBAL_SLEEP)))
                time.sleep(GLOBAL_SLEEP)
                engine.refresh()
                logging.warning("Refresh page.")
                return globalUpdateRegion(engine,attempt)
            else:
                logging.error("I can`t switch to next region. Global error ")
                raise Exception("I can`t switch to next region. Global error ")

        pass

    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver.Chrome(options=None)

    regions = updateRegion(driver)

    for i in range(len(regions)):

        inf = str("")
        inf += str("Passed: ") + str(statistics["passed"])
        inf += str(" Successful: ")+str(statistics["successful"])
        inf += str(" Pages: ") + str(statistics["pages"])
        inf += str(" Regions:") + str(statistics["regions"])

        logging.info(inf)


        catalogRegion = os.path.join(outputCatalog,str(i))

        if( not os.path.exists(catalogRegion)):
            os.makedirs(catalogRegion)

        try:
            if (checkIgnore(regions[i].text)):
                continue

            regions[i].click()

            #Update vacancy list
            def updateVacancy(engine,k = 0):

                try:
                    vacancyBlock = engine.find_element_by_class_name("sticky-container")
                    vacancy = vacancyBlock.find_elements_by_css_selector('div.vacancy-serp-item.vacancy-serp-item_premium')
                    vacancy += vacancyBlock.find_elements_by_css_selector("div.vacancy-serp-item")
                except:
                    time.sleep(TIMESLEEP)
                    experience = k + 1
                    if experience < 10:
                        return updateVacancy(engine, experience)
                    else:
                        logging.error("I can`t update vacancy list")
                        raise Exception("I can`t update vacancy list")
                return vacancy


            def nextPage(engine, k=0):

                if engine == None:
                    raise Exception("I can`t find engine")

                try:
                    buttonContinue = engine.find_element_by_class_name("sticky-container"). \
                        find_element_by_css_selector("a.bloko-button.HH-Pager-Controls-Next.HH-Pager-Control")
                    link = buttonContinue.get_attribute("href")
                    driver.get(link)
                except:

                    try:
                        current_page = driver.find_elements_by_css_selector("span.bloko-button.bloko-button_pressed").text
                        current_page = int(current_page)
                    except:
                        current_page = None

                    try:
                        controls = driver.find_elements_by_css_selector("a.bloko-button.HH-Pager-Control")

                        if(str(controls[-1].text).find('дальше') >= 0):
                            max_page = int(controls[-2].text)
                        else:
                            max_page = int(controls[-1].text)
                    except:
                        max_page = None


                    logging.warning("Next page --> Current page: {} max page: {}".format(str(current_page),str(max_page)))

                    if((current_page < max_page) and max_page != None and current_page != None):

                        logging.warning("Update page. Caller nextPage()")
                        time.sleep(GLOBAL_SLEEP)
                        engine.refresh()

                        experience = k + 1

                        if experience < ATTEMPT_UPDATE:
                            logging.info("I can`t switch to next page. Attempt:{}. Current page:{} Max page: {} ".format(str(experience),str(current_page),str(max_page)))
                            return nextPage(engine,experience)
                        else:
                            logging.error("I can`t switch to next page. Count of attempt bigger {}.  Current page: {} Max page: {}.".format(str(ATTEMPT_UPDATE),str(current_page),str(max_page)))
                            raise Exception("I can`t switch to next page")
                    else:
                        logging.error("I can`t switch to next page.  Current page: {} Max page: {}.".format(str(current_page),str(max_page)))
                        raise Exception("I can`t switch to next page")
                pass

            page = int(1)


            # Proccess
            try:
                findVacancy = int(0)
                while True:

                    try:
                        vacancy = updateVacancy(driver)


                    except:
                        logging.error("I can`t update this page #"+ str(page))

                    pageInformation = list()

                    for j in range(len(vacancy)):

                        tools = list()

                        try:
                            vacancy = updateVacancy(driver)
                        except:
                            logging.error("I can`t update this page #"+ str(page))

                        try:
                            try:
                                city = vacancy[j].find_element_by_css_selector("span.vacancy-serp-item__meta-info").text
                            except:
                                statistics["passed"] += 1
                                city = None


                            try:
                                salary =vacancy[j].find_element_by_css_selector("div.vacancy-serp-item__compensation").text
                            except:
                                salary = str(0)

                            try:
                                language = vacancy[j].find_element_by_css_selector("div.resume-search-item__name").text
                            except:
                                language = "UNKNOWN"

                            current_url = driver.current_url

                            try:
                                a=vacancy[j].find_element_by_css_selector("div.resume-search-item__name").find_element_by_tag_name("a")
                                href = a.get_attribute("href")
                                driver.get(href)

                                #proccess
                                skills = driver.find_elements_by_css_selector("span.Bloko-TagList-Text")

                                for skill in skills:
                                    tools.append(skill.text)

                                driver.back()
                            except:
                                # TMP CODE
                                try:
                                    if(current_url != driver.current_url):
                                        logging.debug("Current url is not valid. Driver.back()")
                                        driver.back()
                                except:
                                    if(current_url != driver.current_url):
                                        logging.debug("Current url is not valid. Driver.back()")
                                        driver.back()

                                vacancy = updateVacancy(driver)
                                tools.append("empty")
                                errText = "I can`t get info about skills. Page: "+str(page) + " vacancy: "+str(j)
                                logging.error(errText)



                            try:
                                latitude, longitude = getLocation(str(city))
                            except:
                                latitude, longitude = 0,0

                            if city != None:
                                pageInformation.append({"city":str(city),"language":str(language), "salary":str(salary), "tools":tools, "latitude":latitude,"longitude":longitude})
                                statistics["successful"] += 1
                                findVacancy += 1

                        except:
                            logging.warning("passed: " + str(city)+" " + str(language) + " " + str(salary)+" "+str(tools))
                            statistics["passed"] += 1
                            continue

                    try:

                        nextPage(driver)
                        statistics["pages"] += 1

                        pageName =str("page")+str(statistics["pages"])+str(".pickle")

                        with open(os.path.join(catalogRegion,pageName),"wb") as f:
                            pickle.dump(pageInformation,f)
                            logging.info(str("Write information in pickle file. Region: {}. Page: {} . Find: {} vacancy.".format(str(i),str(page),str(findVacancy))))

                        page += 1

                    except:
                        logging.error("I can`t switch to next page. Processed page: {}. Region: {}".format(str(page),str(i)))
                        break
            except:
                logging.error("I can`t process this page")

            try:
                regions = globalUpdateRegion(driver)
                statistics["regions"] += 1
            except:
                logging.error("Global exception ! I can`t work")
                raise Exception("Global exception !!! I can`t work")

        except:
            logging.error("EXCEPT ! I can`t switch to next region")
            time.sleep(GLOBAL_SLEEP * 2)
            regions = globalUpdateRegion(driver)
            statistics["regions"] += 1
            continue


    try:
        allSerializeFile = glob(os.path.join(outputCatalog,"**","*.pickle"),recursive=True)

        allInformation = list()

        for sFile in allSerializeFile:

            if(os.path.exists(sFile)):
                with open(sFile,"rb") as f:
                    allInformation += pickle.load(f)
    except:
        logging.error("All information is not available")

    try:
        serializeInformationPath = os.path.join(outputCatalog,"hh.pickle")

        if(os.path.exists(serializeInformationPath)):
            t,h = os.path.split(serializeInformationPath)
            bckPath = os.path.join(t,str(h).split(".")[0],"backup",".pickle")
            os.rename(serializeInformationPath,bckPath)

        with open(serializeInformationPath,"wb") as f:
            pickle.dump(allInformation,f);
    except:
        logging.error("Serialize file is not created")

    pass


# def getLocation(information):
#     locations = list()
#
#     geolocator = Yandex();
#
#     for place in information:
#         try:
#             print("City: "+ str(place['city']))
#             gcode = geolocator.geocode(place["city"])
#             latitude  = gcode.latitude
#             longitude = gcode.longitude
#
#
#             locations.append({"city":place["city"],
#                               "language":place["language"],
#                               "salary":place["salary"],
#                               "tools":place["tools"],
#                               "latitude":latitude,
#                               "longitude":longitude})
#         except:
#             print("Error: "+ str(place['city']))
#             continue
#
#
#     with open("locationshh.pickle","wb") as f:
#
#         pickle.dump(locations,f)
#
#
#     pass

def pushtoMap(information):

    cmap=folium.Map(location=[information[0]["latitude"],information[0]["longitude"]],zoom_start=5)

    for inf in information:
        try:
            latitude = inf["latitude"]
            longitude = inf["longitude"]

            marker = MarkerCluster().add_to(cmap);
            folium.Marker(location=[latitude, longitude],
                          icon=folium.Icon(color='blue', icon='info-sign')).add_to(marker)

        except:
            continue

    cmap.save('index.html')

    # #
    # # for place in information:
    # #     try:
    # #         print("City: "+ str(place['city']))
    # #         gcode = geolocator.geocode(place["city"])
    # #         latitude  = gcode.latitude
    # #         longitude = gcode.longitude
    # #
    # #         folium.Marker(location=[latitude, longitude],
    # #                       icon=folium.Icon(color='blue', icon='info-sign')).add_to(marker)
    # #     except:
    # #         print("Error: "+ str(place['city']))
    # #         continue
    #
    # cmap.save('index.html')

    pass

def main():

    parser = argparse.ArgumentParser(description="Options");
    # parser.add_argument("-s", "--search", help="Keyword for search", action="append", default=None, nargs="*")
    parser.add_argument("-o", "--out", help="Output catalog", default="vacancy")
    parser.add_argument("-p", "--lim_page", help="Limit of page", default=20)
    parser.add_argument("-l", "--load", help="Load serialize data", default=None)
    parser.add_argument("--headless", help="Start with headless ", action="store_true")
    parser.add_argument("--append", help="Append data in exist catalog ", action="store_true")

    args = parser.parse_args()


    if not args.load is None:
        data = DataHunter(path=args.load)
        return True

    hh = HeadHunterScraper(outputCatalog=args.out,use_proxy=True,headless=args.headless)

    try:
        if not args.append :
            hh.process()
        else:
            hh.append()

    except:hh.append()
    finally:hh.dump()

    pass


if __name__ == '__main__':
    main()
