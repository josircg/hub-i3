import os

import requests


def validate_orcid(orcid):
    try:
        response = requests.get('https://orcid.org/' + orcid)
        if response.status_code == 200:
            result = response.text.find('404 - ORCID record not found')
            if result == -1:
                return True
    except ConnectionError:
        return True

    return False


def validate_lattes_id(lattes_id):
    try:
        response = requests.get('https://dgp.cnpq.br/dgp/espelhorh/' + lattes_id)
        if response.status_code == 200:
            # TODO: conferir o nome do pesquisador
            result = response.text.find('/dgp/faces/errorPage.jsf')
            if result == -1:
                return True
    except ConnectionError:
        return True

    return False


def clean_pot_date(filename):
    with open(filename, 'r+') as fp:
        # read an store all lines into list
        lines = fp.readlines()
        # move file pointer to the beginning of a file
        fp.seek(0)
        # truncate the file
        fp.truncate()

        # start writing lines
        for line in lines:
            if not line.startswith('"POT-Creation-Date'):
                fp.write(line)


if __name__ == "__main__":
    for root, dirs, files in os.walk('locale', topdown=True):
        for name in files:
            if name == 'django.po':
                print(os.path.join(root, name))
                clean_pot_date(os.path.join(root, name))
                break
