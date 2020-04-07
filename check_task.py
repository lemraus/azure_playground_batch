#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import azure.batch

from azure.batch import models
from azure.batch.batch_auth import SharedKeyCredentials

import config_resources

import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

def output_tasks_by_job(batch_client):
    jobs = batch_client.job.list()
    for job in jobs:
        #print(job)
        print(f"Sorties des taches du job : {job.id}\n")
        states_tasks = batch_client.job.get_task_counts(job_id = job.id)

        print(f'Nb de tâches total: {states_tasks.completed + states_tasks.running + states_tasks.active}')
        print(f'Tâches finies: {states_tasks.completed} dont {states_tasks.succeeded} réussites et {states_tasks.failed} echecs')
        print(f'Tâches en cours: {states_tasks.running}')
        print(f'Tâches en attente: {states_tasks.active}')
        if states_tasks.active == 0 and states_tasks.running == 0:
            print(f"Recuperation des sorties de l'ensemble des tâches du job {job.id}:")
            output_tasks(job.id)
            print(f"Fin de la recuperation des sorties du job {job.id}")

def output_tasks(job_id):
    tasks = batch_client.task.list(job_id = job_id)
    for task in tasks:
        node_id = batch_client.task.get(job_id = job_id, task_id = task.id).node_info.node_id
        #print("Task: {}".format(task.id))
        #print("Node: {}".format(node_id))
        try:
            write_output(batch_client, job_id, task.id, 'stdout.txt', 'stdout.txt')
        except:
            pass
        try:
            write_output(batch_client, job_id, task.id, 'stderr.txt', 'stderr.txt')
        except:
            pass

def write_output(batch_client, job_id, task_id, path_file, file_name):
    with open(os.path.join(OUTPUT_DIR, f'{job_id}_{task_id}_{file_name}'), 'wb') as file_output:
        output = batch_client.file.get_from_task(
            job_id = job_id,
            task_id = task_id,
            file_path = path_file
        )
        for data in output:
            file_output.write(data)

if __name__ == "__main__" :
    credentials_batch = SharedKeyCredentials(account_name = config_resources.batch['name'], key = config_resources.batch['key'])
    batch_client = azure.batch.BatchServiceClient(credentials = credentials_batch, batch_url = config_resources.batch['url'])
    output_tasks_by_job(batch_client)
