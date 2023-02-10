#!/usr/bin/env python
"""
Script to update Security Policy from a site or a list of sites
This script will:
- Add the internet zone on the device
- Bind the internet zone to all the publicwans
- Update the Security Policy Set assigned to the site

Author: tkamath@paloaltonetworks.com

"""
import sys
import os
import argparse
import time

import cloudgenix
import pandas as pd

GLOBAL_MY_SCRIPT_NAME = "Prisma SD-WAN: Update Security Policy Set + Bind Internet Zone"
GLOBAL_MY_SCRIPT_VERSION = "v1.0"


# Import CloudGenix Python SDK
try:
    import cloudgenix
except ImportError as e:
    cloudgenix = None
    sys.stderr.write("ERROR: 'cloudgenix' python module required. (try 'pip install cloudgenix').\n {0}\n".format(e))
    sys.exit(1)

# Check for cloudgenix_settings.py config file in cwd.
sys.path.append(os.getcwd())
try:
    from cloudgenix_settings import CLOUDGENIX_AUTH_TOKEN

except ImportError:
    # if cloudgenix_settings.py file does not exist,
    # Get AUTH_TOKEN/X_AUTH_TOKEN from env variable, if it exists. X_AUTH_TOKEN takes priority.
    if "X_AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
    elif "AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    else:
        # not set
        CLOUDGENIX_AUTH_TOKEN = None

try:
    # Also, separately try and import USERNAME/PASSWORD from the config file.
    from cloudgenix_settings import CLOUDGENIX_USER, CLOUDGENIX_PASSWORD

except ImportError:
    # will get caught below
    CLOUDGENIX_USER = None
    CLOUDGENIX_PASSWORD = None


# Handle differences between python 2 and 3. Code can use text_type and binary_type instead of str/bytes/unicode etc.
if sys.version_info < (3,):
    text_type = unicode
    binary_type = str
else:
    text_type = str
    binary_type = bytes



site_id_name = {}
site_name_id = {}
securitypolicy_id_name = {}
securitypolicy_name_id = {}
zone_id_name = {}
zone_name_id = {}
site_id_swiidlist = {}
site_id_elemidlist = {}
elem_id_name = {}

def create_dicts(cgx_session):
    #
    # Sites
    #
    print("\tSites")
    resp = cgx_session.get.sites()
    if resp.cgx_status:
        itemlist = resp.cgx_content.get("items", None)
        for item in itemlist:
            site_id_name[item["id"]] = item["name"]
            site_name_id[item["name"]] = item["id"]
    else:
        print("ERR: Could not retrieve sites")
        cloudgenix.jd_detailed(resp)

    #
    # Site WAN Interfaces
    #
    print("\tSite WAN Interfaces")
    for sid in site_id_name.keys():
        resp = cgx_session.get.waninterfaces(site_id=sid)
        if resp.cgx_status:
            itemlist = resp.cgx_content.get("items", None)
            swis = []
            for item in itemlist:
                if item["type"] == "publicwan":
                    swis.append(item["id"])

            site_id_swiidlist[sid] = swis
        else:
            print("ERR: Could not retrieve WAN Interfaces")
            cloudgenix.jd_detailed(resp)

    #
    # Elements
    #
    print("\tElements")
    resp = cgx_session.get.elements()
    if resp.cgx_status:
        itemlist = resp.cgx_content.get("items", None)

        for item in itemlist:
            elem_id_name[item["id"]] = item["name"]
            if item["site_id"] in site_id_elemidlist.keys():
                eids = site_id_elemidlist[item["site_id"]]
                eids.append(item["id"])
                site_id_elemidlist[item["site_id"]] = eids
            else:
                site_id_elemidlist[item["site_id"]] = [item["id"]]

    else:
        print("ERR: Could not retrieve Elements")
        cloudgenix.jd_detailed(resp)

    #
    # Security Policy Sets
    #
    print("\tSecurity Policy Sets")
    resp = cgx_session.get.securitypolicysets()
    if resp.cgx_status:
        itemlist = resp.cgx_content.get("items", None)
        for item in itemlist:
            securitypolicy_id_name[item["id"]] = item["name"]
            securitypolicy_name_id[item["name"]] = item["id"]

    else:
        print("ERR: Could not retrieve Security Policy Sets")
        cloudgenix.jd_detailed(resp)

    #
    # Security Zones
    #
    print("\tSecurity Zones")
    resp = cgx_session.get.securityzones()
    if resp.cgx_status:
        itemlist = resp.cgx_content.get("items", None)
        for item in itemlist:
            zone_id_name[item["id"]] = item["name"]
            zone_name_id[item["name"]] = item["id"]

    else:
        print("ERR: Could not retrieve Security Zones")
        cloudgenix.jd_detailed(resp)

    return


def go():
    """
    Stub script entry point. Authenticates CloudGenix SDK, and gathers options from command line to run do_site()
    :return: No return
    """

    ############################################################################
    # Begin Script, parse arguments.
    ############################################################################
    parser = argparse.ArgumentParser(description="{0} ({1})".format(GLOBAL_MY_SCRIPT_NAME, GLOBAL_MY_SCRIPT_VERSION))


    controller_group = parser.add_argument_group('API', 'These options change how this program connects to the API.')
    controller_group.add_argument("--controller", "-C",
                                  help="Controller URI, ex. https://api.elcapitan.cloudgenix.com",
                                  default=None)

    login_group = parser.add_argument_group('Login', 'These options allow skipping of interactive login')
    login_group.add_argument("--email", "-E", help="Use this email as User Name instead of cloudgenix_settings.py "
                                                   "or prompting",
                             default=None)
    login_group.add_argument("--password", "-PW", help="Use this Password instead of cloudgenix_settings.py "
                                                       "or prompting",
                             default=None)
    login_group.add_argument("--insecure", "-I", help="Do not verify SSL certificate",
                             action='store_true',
                             default=False)
    login_group.add_argument("--noregion", "-NR", help="Ignore Region-based redirection.",
                             dest='ignore_region', action='store_true', default=False)

    config_group = parser.add_argument_group('Config', 'This section provides details on configuration')
    config_group.add_argument("--sitename", "-S", help="Name of the Sitename", default=None)
    config_group.add_argument("--securitypolicy", "-SP", help="Security Policy Set", default=None)
    config_group.add_argument("--filename", "-F", help="CSV file with list of sites. Use header: sitename", default=None)

    debug_group = parser.add_argument_group('Debug', 'These options enable debugging output')
    debug_group.add_argument("--sdkdebug", "-D", help="Enable SDK Debug output, levels 0-2", type=int,
                             default=0)

    args = vars(parser.parse_args())
    ############################################################################
    # Parse and validate arguments
    ############################################################################
    sitename = args["sitename"]
    securitypolicy = args["securitypolicy"]
    filename = args["filename"]
    if filename is None and sitename is None:
        print("ERR: Please provide a sitename or a CSV file")
        sys.exit()

    else:
        if filename is not None:
            if not os.path.exists(filename):
                print("ERR: Invalid file: {}. Please renter file location".format(filename))
                sys.exit()

    sdkdebug = args["sdkdebug"]

    ############################################################################
    # Instantiate API & Login
    ############################################################################

    cgx_session = cloudgenix.API(controller=args["controller"], ssl_verify=False)
    print("{0} v{1} ({2})\n".format(GLOBAL_MY_SCRIPT_NAME, cloudgenix.version, cgx_session.controller))

    # login logic. Use cmdline if set, use AUTH_TOKEN next, finally user/pass from config file, then prompt.
    # figure out user
    if args["email"]:
        user_email = args["email"]
    elif CLOUDGENIX_USER:
        user_email = CLOUDGENIX_USER
    else:
        user_email = None

    # figure out password
    if args["password"]:
        user_password = args["password"]
    elif CLOUDGENIX_PASSWORD:
        user_password = CLOUDGENIX_PASSWORD
    else:
        user_password = None

    # check for token
    if CLOUDGENIX_AUTH_TOKEN and not args["email"] and not args["password"]:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("AUTH_TOKEN login failure, please check token.")
            sys.exit()

    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None

    ############################################################################
    # Create Translation Dicts
    ############################################################################
    create_dicts(cgx_session)

    ############################################################################
    # Validate Configs
    ############################################################################
    sitelist = []
    if sitename is not None:
        if sitename in site_name_id.keys():
            sitelist.append(sitename)
        else:
            print("ERR: Invalid Site Name. Please provide a valid site name")
            sys.exit()

    else:
        data = pd.read_csv(filename)
        columns = data.columns
        if "sitename" in columns:
            sites = data["sitename"].unique()

            for site in sites:
                if site in site_name_id.keys():
                    sitelist.append(site)
                else:
                    print("ERR: Invalid Site Name. Please update the CSV with valid site names")
                    sys.exit()

        else:
            print("ERR: Invalid CSV. Column sitename not found.")
            sys.exit()


    if securitypolicy not in securitypolicy_name_id.keys():
        print("ERR: Invalid Security Policy Set. Please provide a valid Security Policy Set name")
        sys.exit()

    ############################################################################
    # Iterate through sitelist
    # Bind Internet Zone to publicwan
    # Update Security Policy Set
    ############################################################################
    for site in sitelist:
        print("\n\n*********************************\n\n")
        print(site)
        sid = site_name_id[site]

        #
        # Bind Internet Zone to publicwan
        #
        swis = site_id_swiidlist[sid]
        zid = zone_name_id["Internet"]
        eids = site_id_elemidlist[sid]

        for eid in eids:
            data = {
                "zone_id":zid,
                "lannetwork_ids":[],
                "interface_ids":[],
                "wanoverlay_ids":[],
                "waninterface_ids":swis
            }

            resp = cgx_session.post.elementsecurityzones(site_id=sid, element_id=eid, data=data)
            if resp.cgx_status:
                print("\t{}: Internet Zone bound".format(elem_id_name[eid]))

            else:
                print("\tERR: {}: Could not bind security zone".format(elem_id_name[eid]))
                cloudgenix.jd_detailed(resp)

        #
        # Update Security Policy Set
        #
        secpolid = securitypolicy_name_id[securitypolicy]
        resp = cgx_session.get.sites(site_id=sid)
        if resp.cgx_status:
            sdata = resp.cgx_content
            sdata["security_policyset_id"] = secpolid

            resp = cgx_session.put.sites(site_id=sid, data=sdata)
            if resp.cgx_status:
                print("\tSecurity policy updated to {}[{}]".format(securitypolicy, secpolid))
            else:
                print("\tERR: Could not update Security Policy Set !!!")
                cloudgenix.jd_detailed(resp)

        else:
            print("\tERR: Could not retrieve site details")
            cloudgenix.jd_detailed(resp)

        time.sleep(3)

        print("\n\n*********************************")



if __name__ == "__main__":
    go()
