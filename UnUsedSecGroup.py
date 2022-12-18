#!/usr/bin/env python
import boto3
import argparse


def lookup_by_id(sgid):
    sg = ec2.get_all_security_groups(group_ids=sgid)
    return sg[0].name


# get a full list of the available regions
client = boto3.client('ec2')
regions_dict = client.describe_regions()
region_list = [region['RegionName'] for region in regions_dict['Regions']]

# parse arguments
parser = argparse.ArgumentParser(description="Show unused security groups")
parser.add_argument("-r", "--region", type=str, default="us-east-1",
                    help="The default region is us-east-1. The list of available regions are as follows: %s" % sorted(
                        region_list))
parser.add_argument("-d", "--delete", help="delete security groups from AWS", action="store_true")
args = parser.parse_args()

client = boto3.client('ec2', region_name=args.region)
ec2 = boto3.resource('ec2', region_name=args.region)
all_groups = []
security_groups_in_use = []

# Get ALL security groups names
security_groups_dict = client.describe_security_groups()
security_groups = security_groups_dict['SecurityGroups']
for groupobj in security_groups:
    if groupobj['GroupName'] == 'default' or groupobj['GroupName'].startswith('d-') or groupobj['GroupName'].startswith('AWS-OpsWorks-'):
        security_groups_in_use.append(groupobj['GroupId'])
    all_groups.append(groupobj['GroupId'])

# Get all security groups used by instances
instances_dict = client.describe_instances()
reservations = instances_dict['Reservations']
network_interface_count = 0

for i in reservations:
    for j in i['Instances']:
        for k in j['SecurityGroups']:
            if k['GroupId'] not in security_groups_in_use:
                security_groups_in_use.append(k['GroupId'])		

# Security Groups in use by Network Interfaces				
eni_client = boto3.client('ec2', region_name=args.region)
eni_dict = eni_client.describe_network_interfaces()
for i in eni_dict['NetworkInterfaces']:
	for j in i['Groups']:
		if j['GroupId'] not in security_groups_in_use:
			security_groups_in_use.append(j['GroupId'])

# Security groups used by classic ELBs
elb_client = boto3.client('elb', region_name=args.region)
elb_dict = elb_client.describe_load_balancers()
for i in elb_dict['LoadBalancerDescriptions']:
    for j in i['SecurityGroups']:
        if j not in security_groups_in_use:
            security_groups_in_use.append(j)

# Security groups used by ALBs
elb2_client = boto3.client('elbv2', region_name=args.region)
elb2_dict = elb2_client.describe_load_balancers()
for i in elb2_dict['LoadBalancers']:
    for j in i['SecurityGroups']:
        if j not in security_groups_in_use:
            security_groups_in_use.append(j)

# Security groups used by RDS
rds_client = boto3.client('rds', region_name=args.region)
rds_dict = rds_client.describe_db_instances()
for i in rds_dict['DBInstances']:
	for j in i['VpcSecurityGroups']:
		if j['VpcSecurityGroupId'] not in security_groups_in_use:
			security_groups_in_use.append(j['VpcSecurityGroupId'])

delete_candidates = []
for group in all_groups:
    if group not in security_groups_in_use:
        delete_candidates.append(group)

if args.delete:
    print("We will now delete security groups identified to not be in use.")
    for group in delete_candidates:
        security_group = ec2.SecurityGroup(group)
        try:
            security_group.delete()
        except Exception as e:
            print(e)
            print("{0} requires manual remediation.".format(security_group.group_name))
else:
    print("The list of security groups to be removed is below.")
    print("Run this again with `-d` to remove them")
    for group in sorted(delete_candidates):
        print("   " + group)

print("---------------")
print("Activity Report")
print("---------------")

print(u"Total number of Security Groups evaluated: {0:d}".format(len(all_groups)))
print(u"Total number of EC2 Instances evaluated: {0:d}".format(len(reservations)))
print(u"Total number of Load Balancers evaluated: {0:d}".format(len(elb_dict['LoadBalancerDescriptions']) +
                                                                len(elb2_dict['LoadBalancers'])))
print(u"Total number of RDS Instances evaluated: {0:d}".format(len(rds_dict['DBInstances'])))
print(u"Total number of Network Interfaces evaluated: {0:d}".format(len(eni_dict['NetworkInterfaces'])))
print(u"Total number of Security Groups in-use evaluated: {0:d}".format(len(security_groups_in_use)))
if args.delete:
    print(u"Total number of Unused Security Groups deleted: {0:d}".format(len(delete_candidates)))
else:
    print(u"Total number of Unused Security Groups targeted for removal: {0:d}".format(len(delete_candidates)))

    # For each security group in the total list, if not in the "used" list, flag for deletion
    # If running with a "--delete" flag, delete the ones flagged.