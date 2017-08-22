# -*- coding: utf-8 -*-

import json
import pymysql
import uuid
import os
import sys

TYPE_ID = 2


class Crawler:

    lesson_id = ""
    stage_id = ""
    lesson_stage_id = 0
    stage_level_id = 0

    crawl_success = False

    level_code_camp_key = ["id", "level_name", "level_title", "level_description",
                           "level_test", "level_challenge_seed"]

    def __init__(self, path: str):
        self.sql_connection = pymysql.connect(host='localhost',
                                              user='root',
                                              password='wangtian',
                                              db='stemweb',
                                              charset='utf8')
        self.path = path

    def run(self):
        self.crawl()
        self.crawl_success = True
        self.finish()

    def crawl(self):
        lesson_list = os.listdir(self.path)
        for lesson in lesson_list:
            lesson_path = os.path.join(self.path, lesson)
            self.lesson_id = str(uuid.uuid1())
            sql = "INSERT INTO lesson (id, name, typeId) VALUES (%s, %s, %s)"
            self.insert_into_database(sql, (self.lesson_id, lesson[3:].replace('-', ' ').title(), TYPE_ID))
            self.lesson_stage_id = 0
            if not os.path.isfile(lesson_path):
                stage_list = os.listdir(lesson_path)
                for stage in stage_list:
                    self.stage_id = str(uuid.uuid1())
                    sql = "INSERT INTO stage (id, stage_name) VALUES (%s, %s)"
                    self.insert_into_database(sql, (self.stage_id, stage[:-len('.json')].replace('-', ' ').title()))
                    self.lesson_stage_id += 1
                    sql = "INSERT INTO lesson_stage (lesson_id, lesson_stage_order, stage_id) VALUES (%s, %s, %s)"
                    self.insert_into_database(sql, (self.lesson_id, self.lesson_stage_id, self.stage_id))
                    sql = "INSERT INTO stage_sub_stage (stage_id, stage_substage_order, sub_stage_id) VALUES (%s, %s, %s)"
                    self.insert_into_database(sql, (self.stage_id, 1, self.stage_id))
                    stage_path = os.path.join(lesson_path, stage)
                    if stage_path[-len('.json'):] == '.json':
                        with open(stage_path, 'r', encoding="utf8") as stage_file:
                            print(stage_path)
                            data_str = stage_file.read()
                            data = json.loads(data_str)
                            level_list = data['challenges']
                            self.stage_level_id = 0
                            for level in level_list:
                                level_data = {
                                    'id': str(level['id']),
                                    'level_name': str(level['title']) if 'title' in level else None,
                                    'level_title': str(level['title']) if 'title' in level else None,
                                    'level_description': str(json.dumps(level['description'])) if 'description' in level else None,
                                    'level_test': str(json.dumps(level['tests'])) if 'tests' in level else None,
                                    'level_challenge_seed': str(json.dumps(level['challengeSeed'])) if 'challengeSeed' in level else None
                                    }
                                sql = 'INSERT INTO level_code_camp (id, level_name, level_title, level_description, ' \
                                      'level_tests, level_challenge_seed) VALUES (%s, %s, %s, %s, %s, %s)'
                                sql_data = []
                                for i in self.level_code_camp_key:
                                    sql_data.append(level_data[i])
                                self.insert_into_database(sql, tuple(sql_data))
                                sql = 'INSERT INTO level (id, level_name, level_url, type_id) VALUES (%s, %s, %s, %s)'
                                self.insert_into_database(sql, (level_data['id'], level_data['level_name'], '/', TYPE_ID))
                                self.stage_level_id += 1
                                sql = 'INSERT INTO stage_level (stage_id, stage_level_order, level_id) VALUES (%s, %s, %s)'
                                self.insert_into_database(sql, (self.stage_id, self.stage_level_id, level_data['id']))

    def insert_into_database(self, sql: str, data: tuple):
        with self.sql_connection.cursor() as cursor:
            cursor.execute(sql, data)

    def finish(self):
        if self.crawl_success:
            self.sql_connection.commit()
        else:
            self.sql_connection.rollback()
        self.sql_connection.close()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Usage: ' + sys.argv[0] + ' <local json folder path(required)>')
        exit(1)
    crawler = Crawler(sys.argv[1])
    crawler.run()
