#
# Rotina para popular os projetos no Visão
#
import json

import requests

from datetime import datetime, timezone
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from eucs_platform import visao
from projects.models import Project, Topic
from utilities.models import Translation


def create_dataset(auth_header, name, keyword, description, project_list):
    endpoint = settings.VISAO_URL

    record = {
            "name": name,
            "bigAreaId": 12,
            "keyWord": keyword,
            "iconId": 0,
            "description": description,
            "active": True,
            "typeOfLayer": "CIRCLE",
            "permission": "PUBLIC",
            "layers": project_list,
        }

    response = requests.post(f'{endpoint}/api2/group-layers', json=record,
                             timeout=20, verify=False, cookies=auth_header)
    if response.status_code == 200:
        record = response.json()
        return record['id']
    else:
        try:
            record = json.loads(response.content)
            message = record['detail']
        except Exception:
            message = response.status_code
        raise Exception('%s' % message)


def update_dataset(auth_header, id, name, keyword, description, project_list):
    endpoint = settings.VISAO_URL

    record = {
            "id": id,
            "name": name,
            "bigAreaId": 12,
            "iconId": 0,
            "keyWord": keyword,
            "description": description,
            "active": True,
            "typeOfLayer": "CIRCLE",
            "permission": "PUBLIC",
            "layers": project_list,
        }

    response = requests.put(f'{endpoint}/api2/group-layers', json=record,
                            timeout=20, verify=False, cookies=auth_header)
    if response.status_code == 200:
        record = response.json()
        return record['id']
    else:
        try:
            error = json.loads(response.content)
            message = error['message']
        except Exception:
            message = response.status_code
        raise Exception(f'{message}\n{record}')


def update_all():

    tot_updates = Topic.objects.filter(updated=False).count()
    now = datetime.now(timezone.utc).replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%h:%M')
    if tot_updates == 0:
        print(f'Nothing to update {now}')
        return

    auth_header = visao.authenticate2()
    project_list = []
    for project in Project.objects.approved():
        project_layer = visao.create_project_layer(project)
        if project_layer:
            project_list.append(project_layer)

    update_dataset(auth_header,
                   settings.VISAO_LAYER,
                   'Projetos e Iniciativas', 'HUB 3I',
                   'Projetos e Iniciativas da Cívis',
                   project_list)

    for topic in Topic.objects.filter(updated=False):
        if topic.project_set.count() > 0:

            project_list = []
            for project in topic.project_set.approved():
                project_record = visao.create_project_layer(project)
                if project_record:
                    project_list.append(project_record)

            if topic.external_url:
                # obtem o ID do Group Layer
                dataset_id = topic.external_url.split('&')[0][2:]
                update_dataset(auth_header, dataset_id,
                               f'Cívis {topic.topic}',
                               topic.topic,
                               f"Tema {topic.id}",
                               project_list)
            else:
                dataset_id = create_dataset(auth_header, f'Cívis {topic.topic}',
                                            topic.topic, f"Tema {topic.id}", project_list)
                layout = '&amp&ui=f&amp&header=f&amp&hideIndicator=t'
                topic.external_url = f'l={dataset_id}{layout}'
            topic.updated = True
            topic.save()
            print(f'Topic {dataset_id} updated')
        else:
            topic.external_url = None
            topic.updated = True
            topic.save()


def delete_dataset(auth_header, dataset_id):
    tot_excluidos = 0
    endpoint = settings.VISAO_URL
    query = {'groupId.equals': dataset_id}
    response = requests.get(f'{endpoint}/app/api/layers', params=query, verify=False,
                            headers=auth_header)
    if response.status_code == 200:
        result = json.loads(response.text)
        if len(result) > 0:
            for item in result:
                item_id = item['id']
                response = requests.delete(f'{endpoint}/app/api/layers/{item_id}', verify=False, headers=auth_header)
                if response.status_code == 200:
                    tot_excluidos += 1
                else:
                    print('API error %d' % response.status_code)

    response = requests.delete(f'{endpoint}/app/api/group-layers/{dataset_id}', verify=False, headers=auth_header)
    if response.status_code == 200:
        print(f'Group layer deleted. {tot_excluidos} layers deleted')
    else:
        print('Error deleting group layer: %d' % response.status_code)
    return


class Command(BaseCommand):
    label = 'Populate Visão with Project info'

    # topics: include also all topics associated
    # delete_all: delete all dataset projects before insert new ones
    # Deixa de existir por conta da API V2
    def populate_projects(self, topics=False, delete_all=False):
        # Remove todos os projetos existentes
        auth_header = visao.authenticate()
        if delete_all:
            tot_projects = visao.delete_all(auth_header)
            print(f'Projects removed: {tot_projects}')
        tot_projects = 0
        if topics:
            dataset_id = None
        else:
            dataset_id = settings.VISAO_LAYER

        for project in Project.objects.approved():
            visao.save_project(project, auth_header, dataset_id)
            tot_projects += 1
        print(f'Projects added: {tot_projects}')

    def populate_topics(self):
        auth_header = visao.authenticate2()
        count_topics = 0
        count_projects = 0
        for topic in Topic.objects.all():
            if topic.project_set.count() > 0:

                project_list = []
                for project in topic.project_set.approved():
                    project_record = visao.create_project_layer(project)
                    if project_record:
                        project_list.append(project_record)

                dataset_id = create_dataset(auth_header,
                                            f'Cívis {topic.topic}',
                                            topic.topic,
                                            f"Tema {topic.id}",
                                            project_list)
                print(f'Topic={dataset_id}')

                layout = '&amp&ui=f&amp&header=f&amp&hideIndicator=t'
                topic.external_url = f'l={dataset_id}{layout}'
                topic.save()
                count_topics += 1
        print(f'Topics included {count_topics}')
        print(f'Projects included {count_projects}')

    # Cria os datasets dos tópicos em um determinado idioma
    def populate_topics_localized(self):
        auth_header = visao.authenticate()
        ctype = ContentType.objects.get_for_model(Topic)
        count_topics = 0
        count_projects = 0
        domain = settings.DOMAIN
        for record in Translation.objects.filter(language=settings.LANGUAGE_CODE, content_type_id=ctype.id):
            topic = record.content_object

            project_list = []
            for project in topic.project_set.approved():
                project_record = visao.create_project_layer(project)
                if project_record:
                    project_list.append(project_record)

            if topic.external_url is None and topic.project_set.count() > 0:
                dataset_id = create_dataset(auth_header,
                                            record.text,
                                            f"Tema {topic.id}",
                                            f'{domain}/projects?topic={record.text}&id={topic.id}',
                                            project_list)
                print(dataset_id)
                count_topics += 1
                if dataset_id:
                    layout = '&amp&ui=f&amp&header=f&amp&hideIndicator=t'
                    topic.external_url = f'l={dataset_id}{layout}'
                    topic.save()

        print(f'Topics included {count_topics}')
        print(f'Projects included {count_projects}')

    def add_arguments(self, parser):
        parser.add_argument('-a',  '--auth', action="store_true", help='Test authentication')
        parser.add_argument('-cv', '--create_visao', type=str, help='Create new Map (requires Map Name)')
        parser.add_argument('-cd', '--create_dataset', type=str, help='Create new Dataaset')
        parser.add_argument('-i',  '--info', type=int, help='Get Map parameters (requires Group Category ID')
        parser.add_argument('-ct', '--create_topics', action="store_true", help='Create Topics')
        parser.add_argument('-u',  '--update', action="store_true", help='Update All Projects')
        parser.add_argument('-d',  '--delete', type=int, help='Delete Dataset (Group Layer)')

    def handle(self, *args, **options):
        if options['auth']:
            auth_header = visao.authenticate()
            print('Auth ok')

        elif options['info']:
            cookies = visao.authenticate2()
            endpoint = settings.VISAO_URL
            group_id = options['info']
            print('Consultando', endpoint)
            response = requests.get(f'{endpoint}/visao2/api2/grup-categories/{group_id}')
            if response.status_code == 200:
                record = response.json()
                print('VISAO_GROUP=%s' % group_id)
                if len(record['categories']) > 0:
                    category_id = record['categories'][0]['cod']['category']['id']
                    print('VISAO_CATEGORY=%s' % category_id)
                else:
                    print('No category defined for grup-category')
                owner_id = record["ownerId"]
            else:
                print(f'Invalid Group ID (Status Code {response.status_code})')
                exit(-1)

            query = {
                  "id": 0,
                  "geonetworkGroupId": 0,
                  "geonetworkGroupName": "string",
                  "geonetworkAuthorities": {
                    "additionalProp1": [
                      0
                    ],
                    "additionalProp2": [
                      0
                    ],
                    "additionalProp3": [
                      0
                    ]
                  }
                }

            response = requests.post(f'{endpoint}/visao2/api2/session/getUserSessionInfo',
                                     json=query, cookies=cookies)
            if response.status_code == 200:
                record = response.json()
                print('Group Name:', record['geonetworkGroupName'])
                # geo_groupid = record['geonetworkGroupId']
            else:
                print('User Info API failed')
                exit(-1)

            query = {'ownerIdFilter': owner_id, 'type': 'LAYER'}
            response = requests.get(f'{endpoint}/visao2/api2/group-layers', params=query)
            if response.status_code == 200:
                record = response.json()
                if len(record) > 0:
                    print('VISAO_LAYER=%s' % record[0]['id'])
                else:
                    print('No layers found for this user')
            else:
                print('No group layer found for this user')

            print(f'{endpoint}/visao2/viewGroupCategory/{settings.VISAO_GROUP}?l={settings.VISAO_LAYER}'
                  f'&amp&ui=f&amp&header=f&amp&hideIndicator=t')

            # print(f'{endpoint}/visao2/api2/{settings.VISAO_LAYOUT}?' \
            #      f'grupCategory={settings.VISAO_GROUP}' \
            #      f'&l={settings.VISAO_LAYER}&e=f')

        elif options['create_visao']:
            auth_header = visao.authenticate2()
            endpoint = settings.VISAO_URL

            config = [
                {'id': 'zoomInit', 'value': 3.2},
                {'id': 'latInit', 'value': -15.793},
                {'id': 'longInit', 'value': -47.882}
            ]

            record = {
                "about": options['create_visao'],
                "tipoMapa": "NACIONAL",
                "geonetworkGroupId": 5608,
                "config": config
            }
            response = requests.post(f'{endpoint}/visao2/api2/grup-categories', json=record, cookies=auth_header)
            if response.status_code == 200:
                record = response.json()
                group_id = record['id']
                print(f'VISAO_GROUP={group_id}')
            else:
                print('Error inserting new group category')
                exit(-1)

        elif options['create_dataset']:
            auth_header = visao.authenticate2()

            project_list = []
            for project in Project.objects.approved():
                project_layer = visao.create_project_layer(project)
                if project_layer:
                    project_list.append(project_layer)

            dataset_id = create_dataset(auth_header, 'Projetos e Iniciativas', 'HUB 3I',
                                        'Projetos e Iniciativas da Cívis',
                                        project_list)
            print(f'VISAO_LAYER={dataset_id}')

        elif options['create_topics']:
            self.populate_topics()

        elif options['update']:
            update_all()

        elif options['delete']:
            auth_header = visao.authenticate()
            delete_dataset(auth_header, options['delete'])

        elif options['projects']:
            print('Creating/Updating projects')
            self.populate_projects()

        else:
            print('No function specified')
