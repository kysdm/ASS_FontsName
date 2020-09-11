# -*- coding:utf-8 -*-

import os
import shutil
import sqlite3
import logging
from time import strftime, localtime, time
from fontTools.ttLib import TTFont, TTLibError
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
        if not os.path.isfile(dbfile):
            self.dbfile = dbfile
            self.conn = sqlite3.connect(self.dbfile)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                '''create table fontinfo (
                fullname  nvarchar            not null,
                postscript varchar primary key not null,
                enable     char(1)             not null
                );''')
        else:
            self.dbfile = dbfile
            self.conn = sqlite3.connect(self.dbfile)
            self.cursor = self.conn.cursor()

    def Insert(self, fontname, fullname, postscript, enable=1):
        # https://www.liaoxuefeng.com/wiki/1016959663602400/1017598873256736
        try:
            # INSERT OR IGNORE
            self.cursor.execute(f'''insert into fontinfo (fullname, postscript, enable) \
                    values ('{fullname}', '{postscript}', '{enable}')''')
        # except Exception as e:
        except sqlite3.IntegrityError as e:
            log.logger.warning(f'{fontname} ==> {e}')
            self.cursor.close()
            # print(e)
        except Exception as e:
            # log.logger.error(e)
            log.logger.error(f'{fontname} ==> {e}')
            self.cursor.close()
        else:
            self.cursor.close()
            self.conn.commit()
        finally:
            self.conn.close()


def fontinfo(font):
    _FullName = []
    _PostScript = []
    try:
        for v in font.get('name').names:
            if v.nameID == 4:
                # print(f'''Full Name：{v.toUnicode()}''')
                _FullName.append(v.toUnicode())
            elif v.nameID == 6:
                # print(f'''PostScript：：{v.toUnicode()}''')
                _PostScript.append(v.toUnicode())
        return _FullName, _PostScript
    except UnicodeDecodeError as e:
        log.logger.error(e)
        return 1


if __name__ == "__main__":
    abs_path = os.path.split(os.path.realpath(__file__))[0]
    log = Loggers(level='debug')
    dbfile = f'{abs_path}/fontinfo.db'

    for root, dirs, files in os.walk(abs_path):
        for name in files:
            if(name.lower().endswith((".ttf", "otf"))):
                print(f'\n{name}')
                font = TTFont(f'{root}/{name}', fontNumber=0)
                infolist = fontinfo(font)
                if infolist == 1:
                    pass
                    # shutil.move(fontfile, r'C:\ttx\新建文件夹\1')
                else:
                    FullName, PostScript = infolist
                FullName = list(set(FullName))
                PostScript = list(set(PostScript))
                # https://www.runoob.com/python3/python3-att-list-sort.html
                FullName.sort()
                PostScript.sort()
                sql(dbfile).Insert(name, ','.join(
                    FullName), ','.join(PostScript))

            elif(name.lower().endswith(".ttc")):
                print(f'\n{name}')
                i = 0
                while True:
                    try:
                        font = TTFont(f'{root}/{name}', fontNumber=i)
                        infolist = fontinfo(font)
                        if infolist == 1:
                            pass
                            # shutil.move(fontfile, r'C:\ttx\新建文件夹\1')
                        else:
                            # f'FullName{i}', f'PostScript{i}' = infolist
                            # print(type(infolist))
                            exec(f'FullName_{i}, PostScript_{i} = infolist')
                            i += 1
                    except TTLibError as e:
                        if 'specify a font number between 0 and' in str(e):
                            break
                for num in range(i):
                    exec(f'FullName = list(set(FullName_{num}))')
                    exec(f'PostScript = list(set(PostScript_{num}))')
                    # https://www.runoob.com/python3/python3-att-list-sort.html
                    FullName.sort()
                    PostScript.sort()
                    if len(PostScript) != 1:
                        log.logger.debug(f'{name} - ttc?')
                        # print(name)
                    sql(dbfile).Insert(name, ','.join(
                        FullName), ','.join(PostScript))
