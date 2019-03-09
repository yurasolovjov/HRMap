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


def getHHInfo():

    ignoreList = ["Россия"]

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
        getListFromRegions(engine).click()
        getListFromRegions(engine).find_elements_by_tag_name("a")[0].click()
        pass

    def checkIgnore(region):

        for ignore in ignoreList:
            if region == ignore:
                return True

        return  False

    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver.Chrome(options=None)

    information = list()

    url ="https://spb.hh.ru/vacancies/programmist"
    driver.get(url)
    time.sleep(2)

    defaultPage(driver)
    # getListFromRegions(driver).click()
    # link = getListFromRegions(driver).find_elements_by_tag_name("a")[0]
    # link.click()

    getMoreRegion(driver).click()
    regions = getFullRegions(driver).find_elements_by_tag_name("a")

    # search_box = driver.find_element_by_class_name("sticky-container")
    # listRegion = search_box.find_element_by_class_name('clusters-group__items')
    # listRegion.find_element_by_class_name("clusters-list__item_more").click()
    # listRegion = search_box.find_element_by_class_name('clusters-group__items')
    # regions = listRegion

    counterRegion = int(0)

    for i in range(len(regions)):

        try:
            if (checkIgnore(regions[i].text)):
                continue

            regions[i].click()
            # Proccess
            defaultPage(driver)
            getMoreRegion(driver).click()
            regions = getFullRegions(driver).find_elements_by_tag_name("a")
            print("")
        except:
            continue
    pass
    # search_box.click()
    # search_box.send_keys("программист")
    # time.sleep(2)
    # # search_box.send_keys(Keys.ENTER)
    # sform = driver.find_element_by_class_name("search__form")
    # sform.click()
    # sform.send_keys(Keys.ENTER)
    # input_bar = driver.find_element_by_class_name('button__text').find_element_by_tag_name()
    # input_bar.click()
    # input_bar.send_keys(Keys.ENTER)

def getYandexWorkInfo():

    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    driver = webdriver.Chrome(options=None)

    information = list()

    url ="https://rabota.yandex.ru/search?text=%D0%9F%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B8%D1%81%D1%82&rid=225"
    driver.get(url)
    time.sleep(5)

    # search_box = driver.find_element_by_class_name("input__control")
    # search_box.click()
    # search_box.send_keys("программист")
    # time.sleep(2)
    # # search_box.send_keys(Keys.ENTER)
    # sform = driver.find_element_by_class_name("search__form")
    # sform.click()
    # sform.send_keys(Keys.ENTER)

    # input_bar = driver.find_element_by_class_name('button__text').find_element_by_tag_name()
    # input_bar.click()
    # input_bar.send_keys(Keys.ENTER)

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

    a = getHHInfo()
    if(not os.path.exists("base.pickle")):
        loadData = getYandexWorkInfo()
    else:
        with open('base.pickle', "rb") as f:
            loadData = pickle.load(f)

    pushtoMap(loadData)
    pass


if __name__ == '__main__':
    main()
