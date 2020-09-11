# -*- coding:utf-8 -*-

import os
import re
import chardet
import sqlite3
import logging
from time import strftime, localtime, time
# from chardet.universaldetector import UniversalDetector
from logging import Handler, FileHandler, StreamHandler


# https://zhuanlan.zhihu.com/p/75310176
class PathFileHandler(FileHandler):
    def __init__(self, path, filename, mode='a', encoding=None, delay=False):
        filename = os.fspath(filename)
        if not os.path.exists(path):
            os.mkdir(path)
        self.baseFilename = os.path.join(path, filename)
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        if delay:
            Handler.__init__(self)
            self.stream = None
        else:
            StreamHandler.__init__(self, self._open())


class Loggers(object):
    # 日志级别关系映射
    level_relations = {
        'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING,
        'error': logging.ERROR, 'critical': logging.CRITICAL
    }

    def __init__(self, filename=f'''{strftime('%Y%m%d%H%M%S',localtime(time()))}.log''', level='info', log_dir='.',
                 fmt='%(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        abspath = os.path.dirname(os.path.abspath(__file__))
        self.directory = os.path.join(abspath, log_dir)
        format_str = logging.Formatter(fmt)  # 设置日志格式
        self.logger.setLevel(self.level_relations.get(level))  # 设置日志级别
        stream_handler = logging.StreamHandler()  # 往屏幕上输出
        stream_handler.setFormatter(format_str)
        file_handler = PathFileHandler(
            path=self.directory, filename=filename, mode='a')
        file_handler.setFormatter(format_str)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(file_handler)


class sql():
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.conn = sqlite3.connect(self.dbfile)
        self.cursor = self.conn.cursor()
        # if not os.path.isfile(dbfile):
        #     self.cursor.execute(
        #         '''create table fontinfo (
        #         fullname  nvarchar            not null,
        #         postscript varchar primary key not null,
        #         enable     char(1)             not null
        #         );''')

    def Select(self, assfile, fullname):
        # https://www.runoob.com/sqlite/sqlite-like-clause.html
        try:
            # INSERT OR IGNORE
            self.cursor.execute(
                f'''SELECT * FROM "fontinfo" WHERE "fullname" LIKE \'%{fullname}%\'''')
        # except Exception as e:
        except sqlite3.IntegrityError as e:
            log.logger.warning(f'{assfile} ==> {e}')
            self.cursor.close()
            sqlvalue = None
            # print(e)
        except Exception as e:
            # log.logger.error(e)
            log.logger.error(f'{assfile} ==> {e}')
            self.cursor.close()
            sqlvalue = None
        else:
            sqlvalue = self.cursor.fetchall()
            self.cursor.close()
        finally:
            self.conn.close()
        return sqlvalue


def FulltoPs(fullname):
    __resql = sql(dbfile).Select(name, fullname)
    for __fullname in __resql:
        __fullnamelist = __fullname[0].split(',')
        for v in __fullnamelist:
            if v == fullname:
                __postscriptlist = __fullname[1].split(',')
                __enablelist = __fullname[2].split(',')
                if len(__postscriptlist) == 1 and int(__enablelist[0]) == 1:
                    return __postscriptlist[0]
                else:
                    pass


def AssFontReplace(_fontlist, _asstxt):
    for _fullname in _fontlist:
        _postscript = FulltoPs(_fullname)
        if _postscript == None:
            log.logger.warning(f'[{_fullname}] ==> [None]')
        else:
            log.logger.debug(f'[{_fullname}] ==> [{_postscript}]')
            _asstxt = _asstxt.replace(_fullname, _postscript)
    return _asstxt


if __name__ == "__main__":
    abs_path = os.path.split(os.path.realpath(__file__))[0]
    log = Loggers(level='debug')
    dbfile = f'{abs_path}/fontinfo.db'

    for root, dirs, files in os.walk(abs_path):
        for name in files:
            if (name.lower().endswith(".ass")) and (not '.postscript.' in name.lower()):
                log.logger.info(name)
                with open(f'{root}/{name}', 'rb') as f:
                    assbinary = f.read()
                    result = chardet.detect(assbinary)
                asstxt = assbinary.decode(result['encoding']).replace(
                    "\r\n", "\n").replace("\r", "\n")
                pattern_style = re.compile(r'Style: (?:.+?),(.+?),')
                pattern_dialogue = re.compile(
                    r'\\fn(?:\s*?)(.+?)(?:\s*?)(?:\\|})')
                font_style = re.findall(pattern_style, asstxt)
                font_dialogue = re.findall(pattern_dialogue, asstxt)
                font_style.extend(font_dialogue)
                fontlist = []
                for fullname in font_style:
                    if fullname[0] == '@':
                        fontlist.append(fullname[1:])
                    else:
                        fontlist.append(fullname)
                fontlist = list(set(fontlist))
                targetasstxt = AssFontReplace(fontlist, asstxt)
                with open(f'{abs_path}/{os.path.splitext(name)[0]}.PostScript.ass', "w", encoding='UTF-8-SIG', newline='') as f:
                    f.write(targetasstxt)
