#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from time import localtime

import azure.batch

from azure.batch import models
from azure.batch.batch_auth import SharedKeyCredentials

import config_resources

import random

def create_pool(batch_client, name_pool, number_nodes=0, cmd_s_task=None, rule_scale_pool=None):
    #parameter image node
    param_image = models.VirtualMachineConfiguration(
        image_reference = models.ImageReference(
            offer = 'UbuntuServer',
            publisher = 'Canonical',
            sku = '18.04-LTS',
            version = 'latest',
            virtual_machine_image_id = None
        ),
        node_agent_sku_id = 'batch.node.ubuntu 18.04'
    )

    #parameter pool
    new_pool = models.PoolAddParameter(
        id = name_pool, 
        vm_size = 'standard_d1_v2',
        #target_dedicated_nodes = number_nodes,
        virtual_machine_configuration = param_image,
        enable_inter_node_communication = True,
        enable_auto_scale = True,
        auto_scale_formula = rule_scale_pool,
        auto_scale_evaluation_interval = 'PT5M'
        #start_task = s_task
    )

    batch_client.pool.add(new_pool)

def create_job(batch_client, name_job, name_pool, cmd_prep_task=None):
    user = models.UserIdentity(
        auto_user = models.AutoUserSpecification(
            elevation_level = models.ElevationLevel.admin,
            scope = models.AutoUserScope.task
        )
    )

    prepare_task = models.JobPreparationTask(
        command_line = cmd_prep_task,
        id = None,
        user_identity = user
    )

    job = models.JobAddParameter(
        id = name_job,
        pool_info = models.PoolInformation(pool_id = name_pool),
        job_preparation_task = prepare_task
    )
    batch_client.job.add(job)

def create_task(batch_client, name_job, cmd, name_task, param_multi_inst=None):
    current_date = localtime()[0:5]
    current_date = "{0}{1}{2}{3}{4}".format(
        current_date[0],current_date[1],
        current_date[2],current_date[3],
        current_date[4]
    )

    dest_files_in_container = models.OutputFileBlobContainerDestination(
        container_url = f"{config_resources.blob_container['url']}{config_resources.blob_container['sas_token']}",
        path = f"{name_job}/{name_task}/{current_date}"
    )

    dest_files = models.OutputFileDestination(container = dest_files_in_container )

    trigger_upload = models.OutputFileUploadOptions(upload_condition = 'taskCompletion')

    upload_files = models.OutputFile(
        file_pattern = '$AZ_BATCH_TASK_DIR/*' ,
        destination = dest_files,
        upload_options = trigger_upload
    )
    outputs = []
    outputs.append(upload_files)
    tache = models.TaskAddParameter(
        id = name_task, command_line = cmd,
        multi_instance_settings = param_multi_inst,
        resource_files = None, environment_settings = None,
        output_files = outputs
    )
    batch_client.task.add(name_job,tache)

if __name__ == "__main__" :
    credentials_batch = SharedKeyCredentials(account_name = config_resources.batch['name'], key = config_resources.batch['key'])
    batch_client = azure.batch.BatchServiceClient(credentials = credentials_batch, batch_url = config_resources.batch['url'])

    cmd_start_task = (
        "bash -c 'git clone https://github.com/Lemraus/azure_playground_init.git;"
        "cd azure_playground_init; chmod +x install.sh; ./install.sh; cd ..;"
        "git clone https://github.com/Lemraus/azure_playground_src.git'"
    )

    rule_scaling = (
        '// Get pending tasks for the past 5 minutes.\n'
        '$samples = $ActiveTasks.GetSamplePercent(TimeInterval_Minute * 5);\n'
        '// If we have fewer than 70 percent data points, we use the last sample point, otherwise we use the maximum of last sample point and the history average.\n'
        '$tasks = $samples < 70 ? max(0, $ActiveTasks.GetSample(1)) : '
        'max( $ActiveTasks.GetSample(1), avg($ActiveTasks.GetSample(TimeInterval_Minute * 5)));\n'
        '// If number of pending tasks is not 0, set targetVM to pending tasks, otherwise half of current dedicated.\n'
        '$targetVMs = $tasks > 0 ? $tasks : max(0, $TargetDedicatedNodes / 2);\n'
        '// The pool size is capped. This value should be adjusted according to your use case.\n'
        'cappedPoolSize = 5;\n'
        '$TargetLowPriorityNodes = max(0, min($targetVMs, cappedPoolSize));\n'
        '// Set node deallocation mode - keep nodes active only until tasks finish\n'
        '$NodeDeallocationOption = taskcompletion;'
    )

    pool_id = 'CentraleSupelecPool'
    job_id = f"job_grp_2_{random.randint(0, 1e6)}"

    # create_pool(
    #     batch_client = batch_client,
    #     name_pool = pool_id,
    #     number_nodes = 2,
    #     rule_scale_pool = rule_scaling
    # )

    create_job(
        batch_client = batch_client,
        name_job = job_id,
        name_pool = pool_id, 
        cmd_prep_task = cmd_start_task
    )

    multi_instance_task_param = models.MultiInstanceSettings(
        coordination_command_line = (
            "bash -c 'python3 $AZ_BATCH_JOB_PREP_DIR/wd/azure_playground_init/create_host_file.py;"
            "cp $AZ_BATCH_JOB_PREP_DIR/wd/azure_playground_src/script_parallel.py $AZ_BATCH_NODE_SHARED_DIR'"
        ),
        number_of_instances = 2,
        common_resource_files = None
    )
    
    task_id = f"task_{random.randint(0, 1e6)}"

    cmd = "bash -c 'python3 -m scoop --hostfile $AZ_BATCH_NODE_SHARED_DIR/hostfile -vv -n 6 $AZ_BATCH_NODE_SHARED_DIR/script_parallel.py'"

    create_task(
        batch_client = batch_client,
        name_job = job_id,
        cmd = cmd,
        name_task = task_id,
        param_multi_inst = multi_instance_task_param
    )
