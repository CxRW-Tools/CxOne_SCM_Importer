# CxOne SCM Importer Usage Guide

## Summary

CxOne SCM Importer is a specialized tool designed to facilitate the integration of Git repositories into Checkmarx One as SCM projects. This tool streamlines the process of checking if a project already exists, creating a new project if needed, and converting it from a manual project to an SCM project.

## Syntax and Arguments

Execute the script using the following command line:

```
python cxone_scm_importer.py --base_url BASE_URL --tenant_name TENANT_NAME --api_key API_KEY --repo_url REPO_URL --scm_token SCM_TOKEN --scm_org SCM_ORG --project_name PROJECT_NAME [OPTIONS]
```

### Required Arguments

- `--base_url`: The base URL of the Checkmarx One region.
- `--tenant_name`: Your tenant name in Checkmarx One.
- `--api_key`: Your API key for authenticating with the Checkmarx One APIs.
- `--repo_url`: The URL of the Git repository to import.
- `--scm_token`: Personal access token for the SCM (Source Control Management) system.
- `--scm_org`: The SCM organization in which the repositories for this project are located.
- `--project_name`: The name of the Checkmarx One project to create or manage.

### Optional Arguments

- `--iam_base_url`: Optional IAM base URL. Defaults to the same as `base_url` if not provided.
- `--groups`: Comma-separated groups for the project. (e.g., "group1,group2")
- `--tags`: Comma-separated tags for the project. (e.g., "tag1,tag2")
- `--debug`: Enable debug output. (Flag, no value required)

## Usage Examples

Creating a new SCM project in Checkmarx One:

```
python cxone_scm_importer.py --base_url https://cxone.example.com --tenant_name mytenant --api_key 12345 --repo_url https://github.com/user/repo --scm_token ghp_ABC123 --scm_org MyOrg --project_name MyProject
```

Creating a new SCM project with additional groups and tags:

```
python cxone_scm_importer.py --base_url https://cxone.example.com --tenant_name mytenant --api_key 12345 --repo_url https://github.com/user/repo --scm_token ghp_ABC123 --scm_org MyOrg --project_name MyProject --groups "dev,qa" --tags "frontend,backend"
```

Creating a new SCM project with debug output:

```
python cxone_scm_importer.py --base_url https://cxone.example.com --tenant_name mytenant --api_key 12345 --repo_url https://github.com/user/repo --scm_token ghp_ABC123 --scm_org MyOrg --project_name MyProject --debug
```

## Output

The CxOne SCM Importer will provide console output indicating the steps being performed, such as authentication, project existence check, project creation, and conversion to SCM project. If the `--debug` flag is used, additional diagnostic information will be displayed to assist in troubleshooting and verifying the process.


## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
