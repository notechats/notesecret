import hashlib
import logging
import os
import time

from sqlalchemy import BIGINT, Column, String, Table, create_engine, select

from notesecret.base import BaseTable, meta
from notesecret.fernet import decrypt, encrypt

local_secret_path = '~/.secret'
logger = logging.getLogger('tool')


def set_secret_path(path):
    global local_secret_path
    local_secret_path = path


def get_md5_str(strs: str):
    """
    计算字符串md5值
    :param string: 输入字符串
    :return: 字符串md5
    """
    m = hashlib.md5()
    m.update(strs.encode())
    return m.hexdigest()


def get_md5_file(path, chunk=1024 * 4):
    m = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            m.update(data)

    return m.hexdigest()


class SecretManage(BaseTable):
    def __init__(self, secret_dir=None, url=None, cipher_key=None, *args, **kwargs):
        self.cipher_key = cipher_key
        if url is not None:
            uri = url
        else:
            secret_dir = secret_dir or local_secret_path
            secret_dir = secret_dir.replace("~", os.environ['HOME'])
            uri = f'sqlite:///{secret_dir}/.secret_v2.db'

        engine = create_engine(uri)
        logging.info(f'uri:{uri}')

        super(SecretManage, self).__init__(table_name='secret_manage', engine=engine, *args, **kwargs)
        self.table = Table(self.table_name, meta,
                           #Column('secret_key', String(100), comment='secret_key'),
                           Column('cate1', String, comment='cate1', default='', primary_key=True),
                           Column('cate2', String, comment='cate2', default='', primary_key=True),
                           Column('cate3', String, comment='cate3', default='', primary_key=True),
                           Column('cate4', String, comment='cate4', default='', primary_key=True),
                           Column('cate5', String, comment='cate4', default='', primary_key=True),
                           Column('value', String, comment='value', default=''),
                           Column('expire_time', BIGINT, comment='expire_time', default=9999999999),
                           extend_existing=True,
                           )

    def encrypt(self, text):
        """
        加密，我也没测试过，不知道能不能正常使用，纯字母的应该没问题，中文的待商榷
        :param text: 需要加密的文本
        :return: 加密后的文本
        """
        return encrypt(text, self.cipher_key)

    def decrypt(self, encrypted_text):
        """
        解密，我也没测试过，不知道能不能正常使用，纯字母的应该没问题，中文的待商榷
        :param encrypted_text: 需要解密的文本
        :return:解密后的文本
        """
        return decrypt(encrypted_text, self.cipher_key)

    def read(self, cate1, cate2='', cate3='', cate4='', cate5='', value=None, save=True, secret=False,
             expire_time=None):
        """
        按照分类读取保存的key，如果为空或者已过期，则返回None
        :param cate1: cate1
        :param cate2: cate2
        :param cate3: cate3
        :param cate4: cate4
        :param cate5: cate5
        :param value: 保存的数据
        :param save: 是否需要保存，保存的话，会覆盖当前保存的数据
        :param secret: 是否需要加密，如果加密的话，构造类的时候，cipher_key不能为空，这是加密解密的秘钥
        :param expire_time: 过期时间，unix时间戳，如果小于10000000的话，会当做保存数据的持续时间，加上当前的Unix时间戳作为过期时间
        :return: 保存的数据
        """
        if expire_time is not None and expire_time < 1000000000:
            expire_time += int(time.time())
        if save:
            self.write(value, cate1, cate2, cate3, cate4, cate5, secret=secret, expire_time=expire_time)
        if value is not None:
            return value

        sql = select(self.table.columns.value, self.table.columns.expire_time).where(
            self.table.columns.cate1 == cate1,
            self.table.columns.cate2 == cate2,
            self.table.columns.cate3 == cate3,
            self.table.columns.cate4 == cate4,
            self.table.columns.cate5 == cate5
        )
        data = [line for line in self.engine.execute(sql)]
        if len(data) > 0:
            value, expire_time = data[0]
            if secret:
                value = self.decrypt(value)
            if expire_time is None or expire_time == 'None' or int(time.time()) < expire_time:
                return value

        return None

    def write(self, value, cate1, cate2='', cate3='', cate4='', cate5='', secret=False, expire_time=99999999):
        """
        对数据进行保存
        :param value: 保存的数据
        :param cate1:cate1
        :param cate2:cate2
        :param cate3:cate3
        :param cate4:cate4
        :param cate5:cate5
        :param secret: 是否需要加密
        :param expire_time:过期时间，默认不过期
        """
        if value is None:
            return
        if expire_time is not None and expire_time < 1000000000:
            expire_time += int(time.time())
        if secret:
            value = self.encrypt(value)

        properties = {
            "cate1": cate1, "cate2": cate2,
            "cate3": cate3, "cate4": cate4,
            "cate5": cate5, "value": value,
            "expire_time": expire_time
        }

        self.upsert(values=properties)


def read_secret(cate1, cate2='', cate3='', cate4='', cate5='', value=None, save=True, secret=False,
                expire_time=9999999):
    manage = SecretManage()
    manage.create()
    value = manage.read(cate1=cate1, cate2=cate2, cate3=cate3, cate4=cate4, cate5=cate5, value=value, save=save,
                        secret=secret, expire_time=expire_time)
    return value


def write_secret(value, cate1, cate2='', cate3='', cate4='', cate5='', secret=False, expire_time=9999999):
    manage = SecretManage()
    manage.create()
    manage.write(value=value, cate1=cate1, cate2=cate2,
                 cate3=cate3, cate4=cate4, cate5=cate5, secret=secret, expire_time=expire_time)


def save_secret_str(path='~/.secret/secret_str'):
    path = path.replace('~', os.environ['HOME'])
    manage = SecretManage()

    res = []

    all_data = manage.select_all()
    keys = all_data.keys()
    for line in all_data:
        r1 = []
        for i, key in enumerate(keys):
            r1.append(f'{key}\003{line[i]}')
        res.append('\002'.join(r1))
    res = '\001'.join(res)
    with open(path, 'w') as f:
        f.write(res)
    return res


def load_secret_str(secret_str=None, path='~/.secret/secret_str'):
    path = path.replace('~', os.environ['HOME'])
    manage = SecretManage()
    if secret_str is None:
        if not os.path.exists(path):
            print(f'{path} is not exists.')
            return
        with open(path, 'r') as f:
            secret_str = f.read()

    for line in secret_str.split('\001'):

        p = {}
        for kv in line.split('\002'):
            k, v = kv.split('\003')
            if v == 'None':
                v = None
            p[k] = v
        manage.write(**p)
