import requests
from hashlib import md5


def hash_file(path):
    with open(path, 'rb') as fd:
        m = md5()
        m.update(fd.read())

    return m.digest()


def hash_url(url):
    response = requests.get(url, stream=True)

    with open('temp.zip', 'wb') as fd:
        for chunk in response.iter_content(chunk_size=1024):
            fd.write(chunk)

    return hash_file('temp.zip')
