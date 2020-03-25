
                                                    ##########################
                                                    #  Tutorial Azure Batch  #
                                                    ##########################

I. File list
------------

check_task.py            Checks the status of a job's tasks and downloads the stderr/stdout outputs if all tasks are finished.
create_resource.py       Creating a resource group containing a batch account and a storage account that has a blob container.
config_resources.py      Containing information about the batch account and the blob container that will have been created.
config.py                Containing information about service principal and id subscription.
demo_azure_batch/        Contains all the scripts downloaded by a node of the pool.
launch_batch.py          Creating in a batch account, a pool, a job and a mpi task.
requirements.txt         List of python packages needed to run check_task.py, create_resource.py and launch_batch.py.



II - Description files
----------------------

  A) check_task.py

1) Login to an Azure batch account (from the information in config_resources.py)
2) Displaying tasks status summary of each job in the batch account
3) If all tasks are finished within a job, the output files (stdout, stderr) will be downloaded


  B) create_resource.py

1) Login to Azure via a service principal (from the information contained in config.py)
2) Creating of a resource group
3) Creating of an Azure storage account in this resource group (Must be unique across Azure)
4) Creating of an Azure batch account in this resource group (Must be unique within the Azure region where the account is created)
5) Creating of a blob container in the Azure storage account
6) Creating of a file named 'config_resources.py'


  C) config_resources.py

This file contains the following information:
- A variable (str) named 'resource_gpe_name' which contains the name of a resource group
- A variable (dict) named 'batch' that contains the name, primary key and url of an Azure batch account
- A variable (dict) named 'blob_container' that contains the url and the token SAS of a Azure blob container


  D) config.py

This file contains the following information:
- A variable (str) named 'subs' which contains the id of a subscription
- A variable (dict) named 'sp' that contains the client id, name, password and tenant of a service principal


  E) demo_azure_batch/

This folder contains 3 files:
- install.sh (installs all the packages needed to perform the task)
- requirements_node.txt (list of python packages needed to run the task)
- script.py (program executed by the task)


  F) launch_batch.py

1) Login to an Azure batch account (from the information in config_resources.py)
2) Creating of a pool (image: UbuntuServer 18.04-LTS)
    - the inter-node communication is activated
    - the pool grows (up to 2 nodes) and decreases according to the number of tasks via the definition of an autoscaling rule
3) Creating a job
    - added a preparation task that clones a repo git (repo content == content of demo_azure_batch folder) and runs an installation script inside it
            => Executed in user Admin task
4) Creating an mpi task
   - When the task is finished, the output is stored in the blob container of the Azure storage account.


  G) requirements.py

List of python packages needed to run check_task.py, create_resource.py and launch_batch.py.



III - Prerequisites
-------------------

  A) Have an Azure subscription and a service principal

If you don't have a service principal, run the following commands:
az login                                                # Login to Microsoft Azure
az account set -s id_subscription                       # Set a subscription to be the current active subscription
az ad sp create-for-rbac -n new_service_principal       # Creating service principal
    => Store service principal information in a file


  B) Install python 3.7 and packages needed

sudo apt install python3-pip -y
pip3 install -r requirements.txt



IV - Add service principal and subscription information in config.py
--------------------------------------------------------------------

In config.py:
  - Replace value's variable 'subs' by id of your subscription
  - Replace the information contained in 'sp' variable with that of your service principal.



IV - Execute create_resource.py and await completion of execution
-----------------------------------------------------------------

command: python3 create_resource.py

usage: create_resource.py [-h] [--resource_gp_name RESOURCE_GPE_NAME]
                          [--batch_account_name BATCH_ACCOUNT_NAME]
                          [--storage_account_name STORAGE_ACCOUNT_NAME]
                          [--blob_container_name BLOB_CONTAINER_NAME]
                          [--region_name REGION_NAME]

Creating a resource group containing a batch account and a storage account
that has a blob container.

optional arguments:
  -h, --help            show this help message and exit
  --resource_gp_name RESOURCE_GPE_NAME
                        Name of resource group (default: group-centrale-
                        supelec)
  --batch_account_name BATCH_ACCOUNT_NAME
                        Name of batch account (default: ab03centralesupelec)
  --storage_account_name STORAGE_ACCOUNT_NAME
                        Name of storage account (default: as03centralesupelec)
  --blob_container_name BLOB_CONTAINER_NAME
                        Name of blob container (default: results)
  --region_name REGION_NAME
                        Location where resources will be created (default:
                        centralus)

Returns a file named "config_resources.py" containing information about the
batch account and the blob container that will have been created.



V - Execute launch_batch.py
---------------------------

command: python3 launch_batch.py



VI (Optional) - Check status tasks
---------------------------------

command: python3 check_task.py




