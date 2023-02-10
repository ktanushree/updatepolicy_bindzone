# updatepolicy_bindzone
Script to update Security Policy and bind Internet zone to all publicwans

#### Synopsis
This script is very use-case specific. The script first binds the Internet security zone to all the publicwans on the devices on the site. It then updates the security policy set as provided via the CLI.


#### Requirements
* Active CloudGenix Account
* Python >=3.6
* Python modules:
    * CloudGenix Python SDK >= 6.1.2b1 - <https://github.com/CloudGenix/sdk-python>

#### License
MIT

#### Installation:
 - **Github:** Download files to a local directory, manually run `updatesecuritypolicy.py`. 

### Examples of usage:
Update security policy on a single site:
```
./updatesecuritypolicy.py -S SiteName -SP SecurityPolicySetName
```
Update security policy on sites via a CSV
```
./manageclusters.py -F FILE -SP SecurityPolicySetName
```


Help Text:
```angular2
(base) tkamath$ ./updatesecuritypolicy.py -h
usage: updatesecuritypolicy.py [-h] [--controller CONTROLLER] [--email EMAIL] [--password PASSWORD] [--insecure] [--noregion] [--sitename SITENAME] [--securitypolicy SECURITYPOLICY] [--filename FILENAME] [--sdkdebug SDKDEBUG]

Prisma SD-WAN: Update Security Policy Set + Bind Internet Zone (v1.0)

optional arguments:
  -h, --help            show this help message and exit

API:
  These options change how this program connects to the API.

  --controller CONTROLLER, -C CONTROLLER
                        Controller URI, ex. https://api.elcapitan.cloudgenix.com

Login:
  These options allow skipping of interactive login

  --email EMAIL, -E EMAIL
                        Use this email as User Name instead of cloudgenix_settings.py or prompting
  --password PASSWORD, -PW PASSWORD
                        Use this Password instead of cloudgenix_settings.py or prompting
  --insecure, -I        Do not verify SSL certificate
  --noregion, -NR       Ignore Region-based redirection.

Config:
  This section provides details on configuration

  --sitename SITENAME, -S SITENAME
                        Name of the Sitename
  --securitypolicy SECURITYPOLICY, -SP SECURITYPOLICY
                        Security Policy Set
  --filename FILENAME, -F FILENAME
                        CSV file with list of sites. Use header: sitename

Debug:
  These options enable debugging output

  --sdkdebug SDKDEBUG, -D SDKDEBUG
                        Enable SDK Debug output, levels 0-2
(base) tkamath$ 


```

#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **1.0.0** | **b1** | Initial Release. |


#### For more info
 * Get help and additional Prisma SDWAN Documentation at <https://docs.paloaltonetworks.com/prisma/prisma-sd-wan>
 
