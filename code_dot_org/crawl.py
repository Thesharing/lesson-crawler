# -*- coding: utf-8 -*-

from selenium import webdriver
import bs4
import json
import pymysql
import uuid
import sys
import getopt
from enum import Enum


class LevelType(Enum):
    NONE = 0
    CODE_ORG = 1
    CODE_CAMP = 2
    QUIZ = 3
    VIDEO = 4


class LessonType(Enum):
    NONE = 0
    CODE_ORG = 1
    CODE_CAMP = 2


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

    def __init__(self, url: str, lesson_name: str = "Lesson", webdriver_local_path: str = None):
        self.url = url
        self.lesson_id = str(uuid.uuid1())
        self.lesson_name = lesson_name
        self.browser = webdriver.Chrome(
            webdriver_local_path) if webdriver_local_path is not None else webdriver.Chrome()
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
        self.store_lesson()
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
                    title_text, data_option, script_src, level_type = self.crawl_page(a.attrs['href'])
                    if level_type is LevelType.CODE_ORG:
                        self.stage_level_order += 1
                        print("CODE.ORG Stage:", self.lesson_stage_order, "Sub Stage:", self.stage_sub_stage_order,
                              "Level:", self.stage_level_order, "Link: ", a.attrs['href'],
                              "Title: ", title_text, "Length: ", len(data_option))
                        self.store_code_org_level(title_text, script_src, data_option)
                    elif level_type is LevelType.QUIZ:
                        if self.store_quiz_level(title_text, data_option):
                            print("QUIZ Stage:", self.lesson_stage_order, "Sub Stage:", self.stage_sub_stage_order,
                                  "Level:", self.stage_level_order, "Link: ", a.attrs['href'],
                                  "Title: ", title_text)
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
        level_type = LevelType.NONE
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
                    level_type = LevelType.CODE_ORG
        if level_type is not LevelType.CODE_ORG:
            for i in script_list:
                if 'appOptions' in i.text:
                    data_option = i.text[i.text.find('{"level":'):i.text.find('};') + 1]
                    level_type = LevelType.QUIZ
        return title_text, data_option, script_src, level_type

    def store_code_org_level(self, title_text, script_src, data_option):
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
                      'skip_sound': data['dialog']['skipSound'] if 'dialog' in data and 'skipSound' in data[
                          'dialog'] else False,
                      'skip_level': False,
                      'skip_dialog': not data['dialog'][
                          'shouldShowDialog'] if 'dialog' in data and 'shouldShowDialog' in data['dialog'] else True,
                      'pre_title': data['dialog']['preTitle'] if 'dialog' in data and 'preTitle' in data[
                          'dialog'] else None,
                      'level_type': data['dialog']['app'] if 'dialog' in data and 'app' in data['dialog'] else None,
                      'script_src': script_src
                      }
        sql_data = []
        for key in self.level_key_list:
            sql_data.append(level_data[key])
        sql = "INSERT INTO `level_code_org` (`id`, `level_name`, `level_url`, `game_name`, `skin_name`, `base_url`, " \
              "`app_name`,`level_properties`, `script_id`, `script_name`, `stage_position`, `level_position`," + \
              "`has_contained_levels`, `skip_sound`, `skip_level`, `skip_dialog`, `pre_title`," + \
              "`level_type`, `script_src`) VALUES (" + "%s, " * (len(self.level_key_list) - 1) + "%s)"
        self.insert_into_database(sql, tuple(sql_data))
        sql = "INSERT INTO `level` (`id`, `level_name`, `level_url`, `type_id`) VALUES (%s, %s, %s, %s)"
        self.insert_into_database(sql,
                                  (level_data['id'], title_text, level_data['level_url'], LevelType.CODE_ORG.value))
        sql = "INSERT INTO `stage_level` (`stage_id`, `stage_level_order`, `level_id`) VALUES (%s, %s, %s)"
        self.insert_into_database(sql, (self.sub_stage_id, self.stage_level_order, level_data['id']))

    def store_quiz_level(self, title_text, data_option):
        try:
            data = json.loads(data_option)
        except json.JSONDecodeError:
            print("JSON ERROR: " + data_option)
            return False
        questions = []
        answers = []
        app = None
        content = ''
        if 'dialog' in data:
            if 'app' in data['dialog']:
                app = data['dialog']['app']
        if app != 'multi':
            return False
        if 'level' in data:
            if 'questions' in data['level']:
                q = data['level']['questions']
                for i in q:
                    if 'text' in i:
                        text = i['text']
                        questions.append(self.generate_html(text))
            if 'answers' in data['level']:
                a = data['level']['answers']
                for i in a:
                    if 'text' in i:
                        i['text'] = self.generate_html(i['text'])
                    answers.append(i)
            i = 1
            while True:
                if 'content' + str(i) in data['level']:
                    content += self.generate_html(data['level']['content' + str(i)].strip(', 500'))
                    i += 1
                else:
                    break

        self.stage_level_order += 1
        question_id = self.generate_uuid('question', 'id')
        sql = "INSERT INTO `question` (`id`, `questions`, `answers`, `title`, `content`, `app`) VALUES" \
              " (%s, %s, %s, %s, %s, %s)"
        self.insert_into_database(sql,
                                  (question_id, json.dumps(questions), json.dumps(answers), title_text, content, app))
        level_id = self.generate_uuid('level', 'id')
        sql = "INSERT INTO `level_quiz` (`id`, `level_name`) VALUES (%s, %s)"
        self.insert_into_database(sql, (level_id, title_text))
        sql = "INSERT INTO `quiz_question` (`quiz_id`, `question_id`, `order`) VALUES (%s, %s, %s)"
        self.insert_into_database(sql, (level_id, question_id, 0))
        sql = "INSERT INTO `level` (`id`, `level_name`, `level_url`, `type_id`) VALUES (%s, %s, %s, %s)"
        self.insert_into_database(sql, (level_id, title_text, "/", LevelType.QUIZ.value))
        sql = "INSERT INTO `stage_level` (`stage_id`, `stage_level_order`, `level_id`) VALUES (%s, %s, %s)"
        self.insert_into_database(sql, (self.sub_stage_id, self.stage_level_order, level_id))
        return True

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

    def store_lesson(self):
        sql = "INSERT INTO `lesson` (`id`, `name`, `typeId`) VALUES (%s, %s, %s)"
        self.insert_into_database(sql, (self.lesson_id, self.lesson_name, LessonType.CODE_ORG.value))

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

    def generate_html(self, text):
        if len(text) >= 5:
            pos_png = text.find('.png')
            if pos_png >= 0:
                return '<img src=\'' + text[:pos_png + 4].replace('script_assets', 'assets/media/stemweb/lessons/code_org') + '\'></img>'
        return '<p>' + text + '</p>'

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
            if self.sql_connection:
                self.sql_connection.close()
            if self.browser:
                self.browser.close()
                self.browser.quit()


if __name__ == '__main__':
    opt_str = 'Usage: ' + sys.argv[0] + ' <URL (required)> <Lesson Name (required)> -w <Webdriver Path (optional)>'
    driver_path = None
    lesson_id = None
    if len(sys.argv) <= 2:
        print(opt_str)
        exit(1)
    if len(sys.argv) >= 3:
        opts = None
        try:
            opts, args = getopt.getopt(sys.argv[3:], "hw:")
        except getopt.GetoptError:
            print(opt_str)
            exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print(opt_str)
                exit(0)
            elif opt == '-w':
                driver_path = arg
        if driver_path is not None:
            crawler = Crawler(url=sys.argv[1], lesson_name=sys.argv[2], webdriver_local_path=driver_path)
        else:
            crawler = Crawler(url=sys.argv[1], lesson_name=sys.argv[2])
    else:
        crawler = Crawler(url=sys.argv[1], lesson_name=sys.argv[2])
    crawler.run()
