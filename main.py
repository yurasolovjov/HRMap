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
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
import logging
import argparse
from glob2 import glob

ATTEMPT_UPDATE = int(5)
TIMESLEEP = int(1)

def getHHInfo(args):

    outputCatalog = args.out

    if(not os.path.exists(outputCatalog)):
        os.makedirs(outputCatalog)


    logging.basicConfig(filename="HH.log",level=logging.INFO,filemode="w")

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
            time.sleep(TIMESLEEP)
            logging.warning("I can`t update regions. Attempt: #"+str(attempt))

            if ( attempt < ATTEMPT_UPDATE):
                return updateRegion(engine,attempt)
            else:
                logging.error("I can`t update regions. Break")
                raise Exception("I can`t update regions. Break")

        return regions


    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver.Chrome(options=None)

    information = list()

    regions = updateRegion(driver)

    for i in range(len(regions)):

        inf = str("")
        inf += str("Passed: ") + str(statistics["passed"])
        inf += str(" Successful: ")+str(statistics["successful"])
        inf += str(" Pages: ") + str(statistics["pages"])
        inf += str(" Regions:") + str(statistics["regions"])

        logging.info(inf)

        chunkInformation = list()
        catalogRegion = os.path.join(outputCatalog,str(i))

        if( not os.path.exists(catalogRegion)):
            os.makedirs(catalogRegion)

        try:
            if (checkIgnore(regions[i].text)):
                continue

            regions[i].click()

            #Update vacancy list
            def updateVacancy(engine, k = 0):

                try:
                    vacancyBlock = engine.find_element_by_class_name("sticky-container")
                    vacancy = vacancyBlock.find_elements_by_css_selector('div.vacancy-serp-item.vacancy-serp-item_premium')

                    if(len(vacancy) == 0):
                        vacancy = vacancyBlock.find_elements_by_css_selector("div.vacancy-serp-item")
                except:
                    time.sleep(TIMESLEEP)
                    experience = k + 1
                    if experience < 5:
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
                    time.sleep(TIMESLEEP)
                    experience = k + 1
                    if experience < 3:
                        logging.info("I can`t switch to next page. Attempt: " + str(experience))
                        return nextPage(engine,experience)
                    else:
                        logging.info("I can`t switch to next page")
                        raise Exception("I can`t switch to next page")


            def clickVacancy(engine, k=0):

                if engine == None:
                    raise Exception("I can`t find engine")
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
                    updateVacancy(driver)
                    tools.append("empty")
                    errText = "I can`t get info about skills. Page: "+str(page) + " vacancy: "+str(j)
                    logging.error(errText)
                    raise Exception(errText)




            page = int(1)

            # Proccess
            try:
                while True:

                    try:
                        vacancy = updateVacancy(driver)
                        time.sleep(TIMESLEEP)
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
                                city = "Region_"+str(i)
                                print("Passed: "+ str(city))

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

                                updateVacancy(driver)
                                tools.append("empty")
                                errText = "I can`t get info about skills. Page: "+str(page) + " vacancy: "+str(j)
                                logging.error(errText)



                            information.append({"city":str(city),"language":str(language), "salary":str(salary), "tools":tools})
                            chunkInformation.append({"city":str(city),"language":str(language), "salary":str(salary), "tools":tools})
                            pageInformation.append({"city":str(city),"language":str(language), "salary":str(salary), "tools":tools})
                            statistics["successful"] += 1

                        except:
                            logging.debug("passed: " + str(city)+" " + str(language) + " " + str(salary)+" "+str(tools))
                            statistics["passed"] += 1
                            continue

                    try:

                        nextPage(driver)
                        statistics["pages"] += 1

                        pageName =str("page")+str(statistics["pages"])+str(".pickle")

                        if(os.path.exists(os.path.join(catalogRegion,pageName))):
                            pageName =str("page")+str(statistics["pages"])+str("dubl")+str(".pickle")

                        with open(os.path.join(catalogRegion,pageName),"wb") as f:
                            pickle.dump(pageInformation,f)

                        page += 1
                    except:
                        logging.error("I can`t switch to next page")
                        break
            except:
                logging.error("I can`t process this page")


            try:
                regions = updateRegion(driver)
                statistics["regions"] += 1
            except:
                logging.error("I can`t switch to next region")

                driver.refresh()
                regions=updateRegion(driver)

        except:
            logging.error("EXCEPT ! I switch to next region")
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

def getYandexWorkInfo():

    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver.Chrome(options=None)

    information = list()

    url ="https://rabota.yandex.ru/search?text=%D0%9F%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B8%D1%81%D1%82&rid=225"
    driver.get(url)
    time.sleep(TIMESLEEP)


    lim = 60

    for i in range(1,100000):
        time.sleep(4)
        try:

            if i > lim:
                break

            content_main =driver.find_element_by_class_name('content-left-main')
            languages = content_main.find_elements_by_class_name('serp-vacancy__name')
            salary = content_main.find_elements_by_class_name('serp-vacancy__salary')
            citys_row = content_main.find_elements_by_class_name('serp-vacancy__contacts')
            # time.sleep(4)

            if (len(languages) != len(salary) or len(salary) != len(citys_row)):
                break;

            for city,lang,sal in zip(citys_row, languages, salary):
                try:
                    textcity = city.find_element_by_class_name('serp-vacancy__address').find_element_by_class_name('address').text
                    information.append({"city":textcity,"language":lang.text, "salary":sal.text})
                except:
                    information.append({"city":str(None),"language":str(None), "salary":str(None)})

            print("Query: "+ str(i))

            next = driver.find_element_by_class_name('pager__links')
            next.find_element_by_class_name('pager__link_next_yes').click()

        except:
            try:
                driver.close()
                break;
            except:
                break;

    with open("yandex.pickle","wb") as f:
        pickle.dump(information,f)

    return information



def pushtoMap(information):

    geolocator = Nominatim()

    centralgcode = geolocator.geocode('Москва')
    latitude = centralgcode.latitude
    longitude = centralgcode.longitude

    cmap=folium.Map(location=[latitude,longitude],zoom_start=5)
    marker = MarkerCluster().add_to(cmap);

    for place in information:
        try:
            print("City: "+ str(place['city']))
            gcode = geolocator.geocode(place["city"])
            latitude  = gcode.latitude
            longitude = gcode.longitude

            folium.Marker(location=[latitude, longitude],
                          icon=folium.Icon(color='blue', icon='info-sign')).add_to(marker)
        except:
            print("Error: "+ str(place['city']))
            continue

    cmap.save('index.html')

    pass

def main():

    parser = argparse.ArgumentParser(description="Options");
    # parser.add_argument("-s", "--search", help="Keyword for search", action="append", default=None, nargs="*")
    parser.add_argument("-o", "--out", help="Output catalog", default="vacancy")
    parser.add_argument("-l", "--lim_page", help="Limit of page", default=20)

    args = parser.parse_args()

    getHHInfo(args)
    # if(not os.path.exists("base.pickle")):
        # loadData = getYandexWorkInfo()
    # else:
    #
    # pushtoMap(loadData)
    pass


if __name__ == '__main__':
    main()
