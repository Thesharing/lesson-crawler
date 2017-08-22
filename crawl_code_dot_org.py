# -*- coding: utf-8 -*-

from selenium import webdriver
import bs4
import json
import pymysql
import uuid
import sys
import getopt

TYPE_ID = 1


class Crawler:

    stage_id = ""
    sub_stage_id = ""
    lesson_stage_order = 1
    stage_sub_stage_order = 1
    stage_level_order = 0

    crawl_success = False

    level_key_list = ['id', 'level_name', 'level_url', 'game_name', 'skin_name', 'base_url', 'app_name',
                      'level_properties', 'script_id', 'script_name', 'stage_position', 'level_position',
                      'has_contained_levels', 'skip_sound', 'skip_level', 'skip_dialog', 'pre_title',
                      'level_type', 'script_src']

    def __init__(self, url: str, webdriver_local_path: str = None, lesson_id: str = str(uuid.uuid1())):
        self.url = url
        self.lesson_id = lesson_id
        self.browser = webdriver.Chrome(webdriver_local_path) if webdriver_local_path is not None else webdriver.Chrome()
        self.sql_connection = pymysql.connect(host='localhost',
                                              user='root',
                                              password='wangtian',
                                              db='stemweb',
                                              charset='utf8')

    def run(self):
        self.crawl_site()
        self.crawl_success = True
        self.finish()

    def crawl_site(self):
        self.browser.get(self.url)

        self.stage_id = self.generate_uuid('stage', 'id')
        self.sub_stage_id = self.generate_uuid('stage', 'id')

        page = self.browser.page_source
        soup = bs4.BeautifulSoup(page, 'lxml')
        table = soup.find('table')
        for idx, tr in enumerate(table.find_all('tr')):
            if idx != 0:
                td_list = tr.find_all('td')
                td = td_list[1]
                a_list = td.find_all('a')
                for a in a_list:
                    if a.text == '线下的活动':
                        if self.stage_sub_stage_order > 1:
                            self.store_stage()
                            self.lesson_stage_order += 1
                            self.stage_sub_stage_order = 1
                        self.stage_id = self.generate_uuid('stage', 'id')
                        continue
                    title_text, data_option, script_src = self.crawl_page(a.attrs['href'])
                    if data_option is not None:
                        self.stage_level_order += 1
                        print("Stage:", self.lesson_stage_order, "Sub Stage:", self.stage_sub_stage_order,
                              "Level:", self.stage_level_order, "Link: ", a.attrs['href'],
                              "Title: ", title_text, "Length: ", len(data_option))
                        self.store_level(title_text, script_src, data_option)
                if self.stage_level_order > 0:
                    self.store_sub_stage()
                    self.stage_sub_stage_order += 1
                    self.stage_level_order = 0
                self.sub_stage_id = self.generate_uuid('stage', 'id')
        if self.stage_sub_stage_order > 1:
            self.store_stage()
            self.stage_id = self.generate_uuid('stage', 'id')
            self.lesson_stage_order += 1
            self.stage_sub_stage_order = 1

    def crawl_page(self, href):
        data_option = None
        script_src = None
        self.browser.get(href)
        page = self.browser.page_source
        soup = bs4.BeautifulSoup(page, 'lxml')
        title = soup.find('title')
        title_text = title.text.strip('Code.org - ')
        body = soup.find('body')
        script_list = body.find_all("script")
        for i in script_list:
            if 'data-appoptions' in i.attrs:
                data_option = i.attrs['data-appoptions']
                if 'src' in i.attrs:
                    script_src = i.attrs['src']
                    script_src = script_src[: script_src.find('.min-')] + '.js'
        return title_text, data_option, script_src

    def store_level(self, title_text, script_src, data_option):
        data = json.loads(data_option)
        level_data = {'id': self.generate_uuid('level', 'id'),
                      'level_name': title_text,
                      'level_url': '/',
                      'game_name': data['levelGameName'] if 'levelGameName' in data else None,
                      'skin_name': data['skinId'] if 'skinId' in data else None,
                      'base_url': data['baseUrl'] if 'baseUrl' in data else None,
                      'app_name': data['app'] if 'app' in data else None,
                      'level_properties': json.dumps(data['level']) if 'level' in data else None,
                      'script_id': data['scriptId'] if 'scriptId' in data else None,
                      'script_name': data['scriptName'] if 'scriptName' in data else None,
                      'stage_position': data['stagePosition'] if 'stagePosition' in data else None,
                      'level_position': data['levelPosition'] if 'levelPosition' in data else None,
                      'has_contained_levels': data['hasContainedLevels'] if 'hasContainedLevels' in data else False,
                      'skip_sound': data['dialog']['skipSound'] if 'dialog' in data and 'skipSound' in data['dialog'] else False,
                      'skip_level': False,
                      'skip_dialog': not data['dialog']['shouldShowDialog'] if 'dialog' in data and 'shouldShowDialog' in data['dialog'] else True,
                      'pre_title': data['dialog']['preTitle'] if 'dialog' in data and 'preTitle' in data['dialog'] else None,
                      'level_type': data['dialog']['app'] if 'dialog' in data and 'app' in data['dialog'] else None,
                      'script_src': script_src
                      }
        sql_data = []
        for key in self.level_key_list:
            sql_data.append(level_data[key])
        sql = "INSERT INTO `level_code_org` (`id`, `level_name`, `level_url`, `game_name`, `skin_name`, `base_url`, " \
              "`app_name`,`level_properties`, `script_id`, `script_name`, `stage_position`, `level_position`," + \
              "`has_contained_levels`, `skip_sound`, `skip_level`, `skip_dialog`, `pre_title`," +\
              "`level_type`, `script_src`) VALUES (" + "%s, " * (len(self.level_key_list) - 1) + "%s)"
        self.insert_into_database(sql, tuple(sql_data))
        sql = "INSERT INTO `level` (`id`, `level_name`, `level_url`, `type_id`) VALUES (%s, %s, %s, %s)"
        self.insert_into_database(sql, (level_data['id'], title_text, level_data['level_url'], TYPE_ID))
        sql = "INSERT INTO `stage_level` (`stage_id`, `stage_level_order`, `level_id`) VALUES (%s, %s, %s)"
        self.insert_into_database(sql, (self.sub_stage_id, self.stage_level_order, level_data['id']))

    def store_sub_stage(self):
        sql = "INSERT INTO `stage` (`id`, `stage_name`) VALUES (%s, %s)"
        self.insert_into_database(sql, (self.sub_stage_id, '子关卡 ' + str(self.stage_sub_stage_order)))
        sql = "INSERT INTO `stage_sub_stage` (`stage_id`, `stage_substage_order`, `sub_stage_id`) VALUES (%s, %s, %s)"
        self.insert_into_database(sql, (self.stage_id, self.stage_sub_stage_order, self.sub_stage_id))

    def store_stage(self):
        sql = "INSERT INTO `stage` (`id`, `stage_name`) VALUES (%s, %s)"
        self.insert_into_database(sql, (self.stage_id, '关卡 ' + str(self.lesson_stage_order)))
        sql = "INSERT INTO `lesson_stage` (`lesson_id`, `lesson_stage_order`, `stage_id`) VALUES (%s, %s, %s)"
        self.insert_into_database(sql, (self.lesson_id, self.lesson_stage_order, self.stage_id))

    def insert_into_database(self, sql: str, data: tuple):
        with self.sql_connection.cursor() as cursor:
            cursor.execute(sql, data)

    def generate_uuid(self, table_name, column_name):
        u = str(uuid.uuid1())
        with self.sql_connection.cursor() as cursor:
            sql = "SELECT " + column_name + " FROM " + table_name + " WHERE " + column_name + " = %s"
            while cursor.execute(sql, u) > 0:
                u = str(uuid.uuid1())
        return u

    def finish(self):
        if self.crawl_success:
            self.sql_connection.commit()
        else:
            self.sql_connection.rollback()
        self.sql_connection.close()
        self.browser.close()
        self.browser.quit()

    def __del__(self):
        if not self.crawl_success:
            self.sql_connection.close()
            self.browser.close()
            self.browser.quit()

if __name__ == '__main__':
    opt_str = 'Usage: ' + sys.argv[0] + ' <URL(required)> -w <webdriver executable path (optional)> -l <lesson id( optional)>'
    driver_path = None
    lesson_id = None
    if len(sys.argv) <= 1:
        print(opt_str)
        exit(1)
    try:
        opts, args = getopt.getopt(sys.argv[2:], "hw:l:")
    except getopt.GetoptError:
        print(opt_str)
        exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(opt_str)
            exit(0)
        elif opt == '-w':
            driver_path = arg
        elif opt == '-l':
            lesson_id = arg
    if driver_path is not None:
        if lesson_id is not None:
            crawler = Crawler(url=sys.argv[1], webdriver_local_path=driver_path, lesson_id=lesson_id)
        else:
            crawler = Crawler(url=sys.argv[1], webdriver_local_path=driver_path)
    elif lesson_id is not None:
        crawler = Crawler(url=sys.argv[1], lesson_id=lesson_id)
    else:
        crawler = Crawler(url=sys.argv[1])
    print(sys.argv[1], driver_path, lesson_id)
    exit()
    crawler.run()
