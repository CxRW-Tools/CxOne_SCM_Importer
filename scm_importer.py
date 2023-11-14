import sys
import json
import requests
import argparse
from urllib.parse import urlparse
import time
import re

# Global variables
base_url = None
tenant_name = None
auth_url = None
iam_base_url = None
auth_token = None
debug = False

def generate_auth_url():
    global iam_base_url
        
    try:
        if debug:
            print("Generating authentication URL...")
        
        if iam_base_url is None:
            iam_base_url = base_url.replace("ast.checkmarx.net", "iam.checkmarx.net")
            if debug:
                print(f"Generated IAM base URL: {iam_base_url}")
        
        temp_auth_url = f"{iam_base_url}/auth/realms/{tenant_name}/protocol/openid-connect/token"
        
        if debug:
            print(f"Generated authentication URL: {temp_auth_url}")
        
        return temp_auth_url
    except AttributeError:
        print("Error: Invalid base_url provided")
        sys.exit(1)

def authenticate(api_key):
    if auth_url is None:
        return None
    
    if debug:
        print("Authenticating with API...")
        
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        'grant_type': 'refresh_token',
        'client_id': 'ast-app',
        'refresh_token': api_key
    }
    
    try:
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        
        json_response = response.json()
        access_token = json_response.get('access_token')
        
        if not access_token:
            print("Error: Access token not found in the response.")
            return None
        
        if debug:
            print("Successfully authenticated")
        
        return access_token
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during authentication: {e}")
        sys.exit(1)

def read_repo_urls(file_path):
    try:
        if debug:
            print(f"Reading repository URLs from file: {file_path}")
        with open(file_path, 'r') as file:
            repo_urls = [line.strip() for line in file]
        if debug:
            print(f"Found {len(repo_urls)} repository URLs")
        return repo_urls
    except Exception as e:
        print(f"An error occurred while reading the repository URLs: {e}")
        sys.exit(1)

def check_project_exists(project_name):
    if debug:
        print(f"Checking if project exists: {project_name}")
    
    headers = {
        'Accept': 'application/json; version=1.0',
        'Authorization': f'Bearer {auth_token}',
    }
    
    params = {
        "name": project_name
    }

    projects_url = f"{base_url}/api/projects/"

    try:
        response = requests.get(projects_url, headers=headers, params=params)
        response.raise_for_status()
        projects = response.json()
        
        # Check if the 'projects' key is not None before iterating
        if projects.get('projects') is not None:
            for project in projects['projects']:
                if project.get('name') == project_name:
                    if debug:
                        print(f"Project found: {project_name}")
                    return project.get('id')
        
        if debug:
            print(f"No project found for: {project_name}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking for project existence: {e}")
        sys.exit(1)

def check_repo_onboarded(repo_url):
    if debug:
        print(f"Checking if a project already exists with {repo_url}")
    
    headers = {
        'Accept': 'application/json; version=1.0',
        'Authorization': f'Bearer {auth_token}',
    }
    
    params = {
        "repo-url": repo_url
    }

    projects_url = f"{base_url}/api/projects/"

    try:
        response = requests.get(projects_url, headers=headers, params=params)
        response.raise_for_status()
        projects = response.json()

        # Check if the 'projects' key is not None before iterating
        if projects.get('projects') is not None:
            for project in projects['projects']:
                if project.get('repoUrl') == repo_url and len(project.get('imported_proj_name')) > 0:
                    if debug:
                        print(f"Repo already in use")
                    return project.get('name')
        
        if debug:
            print(f"No project found using {repo_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking for project existence: {e}")
        sys.exit(1)

def create_project(project_name, repo_url, groups, tags):
    if debug:
        print(f"Creating project: {project_name}")
    
    headers = {
        'Accept': 'application/json; version=1.0',
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json; version=1.0',
        'CorrelationId': ''
    }
    data = {
        "name": project_name,
        "groups": groups,
        "tags": tags,
        "repoUrl": repo_url,
        "origin": "SCM Importer",
        "tags": {
            "SCM Importer": ""
        },
        "criticality": 3
    }
    
    data = {key: list(value) if isinstance(value, set) else value for key, value in data.items()}
    
    projects_url = f"{base_url}/api/projects/"
    
    try:
        response = requests.post(projects_url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while creating the project: {e}")
        if response.content:
            print(f"Response content: {response.content}")
        sys.exit(1)
    
    project_id = response.json().get('id')
    if not project_id:
        print("Error: Project ID not found in the response.")
        return None
    
    if debug:
        print(f"Project {project_name} created successfully with project ID: {project_id}")
    
    return project_id

def is_scm_project(project_id):
    project_url = f"{base_url}/api/projects/{project_id}"
    
    headers = {
        'Accept': 'application/json; version=1.0',
        'Authorization': f'Bearer {auth_token}',
        'CorrelationId': ''
    }
    
    try:
        # Make the GET request to the Checkmarx One API
        response = requests.get(project_url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP error codes

        # Check if the 'repoId' field is in the response to determine SCM project type
        return 'repoId' in response.json()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking if the project is an SCM project: {e}")
        if response.content:
            print(f"Response content: {response.content}")
        sys.exit(1)

def convert_to_scm_project(project_id, repo_url, scm_token, scm_org):
    if debug:
        print(f"Converting project...")

    headers = {
        'Accept': 'application/json; version=1.0',
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json; version=1.0',
        'CorrelationId': ''
    }
    
    # Determine the scmType based on the repo_url
    scm_type = determine_scm_type(repo_url)

    data = {
        "scmType": scm_type,
        "scmOnPremUrl": None,
        "orgIdentity": scm_org,
        "token": scm_token,
        "webhookEnabled": True,
        "autoScanCxProjectAfterConversion": False,
        "projects": [
            {
                "cxProjectId": project_id,
                "scmRepositoryUrl": repo_url,
            }
        ]
    }
    
    conversion_url = f"{base_url}/api/repos-manager/project-conversion"

    try:
        response = requests.post(conversion_url, headers=headers, json=data)
        response.raise_for_status()
        
        body = response.json()
        process_id = body.get('processId')
        message = body.get('message')
        
        if not process_id :
            raise ValueError("Response JSON does not contain 'processId'.")

        if debug:
            print(f"Started conversion process with ID {process_id}")

        return process_id, message

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while converting the project: {e}")
        if response.content:
            print(f"Response content: {response.content}")
        sys.exit(1)
    except ValueError as ve:
        print(f"An error occurred with the response data: {ve}")
        sys.exit(1)

def determine_scm_type(repo_url):
    parsed_url = urlparse(repo_url)
    if "github.com" in parsed_url.netloc:
        return "github"
    elif "gitlab.com" in parsed_url.netloc:
        return "gitlab"
    elif "bitbucket.org" in parsed_url.netloc:
        return "bitbucket"
    elif "azure.com" in parsed_url.netloc:
        return "azure"
    else:
        print("Error: Unsupported SCM type or invalid repository URL.")
        sys.exit(1)

def check_conversion_status(process_id):
    headers = {
        'Accept': 'application/json; version=1.0',
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json; version=1.0',
        'CorrelationId': ''
    }

    status_url = f"{base_url}/api/repos-manager/conversion/status"

    try:
        response = requests.get(status_url, headers=headers, params={'processId': process_id})
        response.raise_for_status()
        status_data = response.json()
        return status_data.get('migrationStatus'), status_data.get('summary')
    except requests.exceptions.HTTPError as e:
        print(f"Error checking conversion status: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def main():
    global base_url
    global tenant_name
    global debug
    global auth_url
    global auth_token
    global iam_base_url

    # Parse and handle various CLI flags
    parser = argparse.ArgumentParser(description='Import a Git repository as an SCM Project using Checkmarx One APIs')
    parser.add_argument('--base_url', required=True, help='Region Base URL')
    parser.add_argument('--iam_base_url', required=False, help='Region IAM Base URL')
    parser.add_argument('--tenant_name', required=True, help='Tenant name')
    parser.add_argument('--api_key', required=True, help='API key for authentication')
    parser.add_argument('--repo_url', required=True, help='Git repository URL to import')
    parser.add_argument('--scm_token', required=True, help='SCM personal access token')
    parser.add_argument('--scm_org', required=True, help='The SCM organization in which the repos for this project are located')
    parser.add_argument('--project_name', required=True, help='Name of CxOne project to create')
    parser.add_argument('--groups', required=False, help='Comma-separated groups for the project', default=None)
    parser.add_argument('--tags', required=False, help='Comma-separated tags for the project', default=None)
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()
    base_url = args.base_url
    tenant_name = args.tenant_name
    repo_url = args.repo_url
    scm_token = args.scm_token
    scm_org = args.scm_org
    project_name = args.project_name
    groups = args.groups.split(',') if args.groups else []
    tags = args.tags.split(',') if args.tags else []
    debug = args.debug
            
    # Authenticate to CxOne
    if args.iam_base_url:
        iam_base_url = args.iam_base_url
    
    auth_url = generate_auth_url()
    auth_token = authenticate(args.api_key)
    
    if auth_token is None:
        return
    
    # Check to see if the project already exists
    project_id = check_project_exists(project_name)

    if project_id is None:
        project_id = create_project(project_name, repo_url, groups, tags)
    else:
        # Check if the existing project is an SCM project; if it is, we can quit
        if is_scm_project(project_id):
            print(f"Project {project_name} already exists as an SCM project!")
            sys.exit(0)
        
    process_id, message = convert_to_scm_project(project_id, repo_url, scm_token, scm_org)

    migration_status, summary = "IN_PROGRESS", ""

    # Loop until the status is not 'IN_PROGRESS'
    while migration_status == "IN_PROGRESS":
        migration_status, summary = check_conversion_status(process_id)
        if migration_status == "IN_PROGRESS":
            if debug:
                print("Conversion in progress...")
            time.sleep(1)
        elif migration_status == "OK":
            print(f"SCM project created for {project_name}.")
            break
        else:
            if debug:
                print(f"Conversion status: {migration_status}")
            existing_project_name = check_repo_onboarded(repo_url)
            if existing_project_name is None:
                print(f"SCM project conversion failed due to unknown error! {summary}")
            else:
                print(f"SCM project conversion failed! The repository {repo_url} is already in use by project {existing_project_name}.")
            sys.exit(1)

  
if __name__ == "__main__":
    main()
