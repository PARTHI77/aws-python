#!/usr/bin/python
import os
import sys
import boto3

ec2 = boto3.resource('ec2')

sgs = list(ec2.security_groups.all())
insts = list(ec2.instances.all())

all_sgs = set([sg.group_name for sg in sgs])
all_inst_sgs = set([sg['GroupName']
                    for inst in insts for sg in inst.security_groups])
unused_sgs = all_sgs - all_inst_sgs

print("Total SGs: ", len(all_sgs))
print("SGS attached to instances: ", len(all_inst_sgs))
print("Orphaned SGs: ", len(unused_sgs))
print("Unattached SG names: ", unused_sgs)
