from cryptography.fernet import Fernet


def generate_key():
    return Fernet.generate_key().decode()


def encrypt(text, cipher_key=None):
    """
    加密，我也没测试过，不知道能不能正常使用，纯字母的应该没问题，中文的待商榷
    :param text: 需要加密的文本
    :param cipher_key: 加密key
    :return: 加密后的文本
    """
    if cipher_key is None or text is None:
        return text
    cipher = Fernet(bytes(cipher_key, encoding="utf8"))
    return cipher.encrypt(text.encode()).decode()


def decrypt(encrypted_text, cipher_key=None):
    """
    解密，我也没测试过，不知道能不能正常使用，纯字母的应该没问题，中文的待商榷
    :param cipher_key: 加密key
    :param encrypted_text: 需要解密的文本
    :return:解密后的文本
    """
    if cipher_key is None or encrypted_text is None:
        return encrypted_text
    cipher = Fernet(bytes(cipher_key, encoding="utf8"))
    try:
        return cipher.decrypt(bytes(encrypted_text, encoding='utf8')).decode()
    except Exception as e:
        return encrypted_text
