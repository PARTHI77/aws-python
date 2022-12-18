# -*- coding: utf-8 -*-

import time
import boto3
import sys
import os

def connect(rname):
    try:
        ec2 = boto3.client("ec2", region_name=rname)
        print 'Connected to EC2 %s Region' % (rname)
    except:
        print sys.exc_info()
    return ec2

def vpc_setup(ec2, vcidr, scidr):
    try:
        vpc = ec2.create_vpc(CidrBlock=vcidr)
        print 'VPC created with ID: %s' % (vpc['Vpc']['VpcId'])

        subnet = ec2.create_subnet(VpcId=vpc['Vpc']['VpcId'], CidrBlock=scidr)
        print 'Subnet created with ID: %s' % (subnet['Subnet']['SubnetId'])

        gateway = ec2.create_internet_gateway()
        print 'Internet Gateway created with ID: %s' % (gateway['InternetGateway']['InternetGatewayId'])

        ec2.attach_internet_gateway(VpcId=vpc['Vpc']['VpcId'],
                  InternetGatewayId=gateway['InternetGateway']['InternetGatewayId'])
        print 'Gateway %s attached to VPC %s' % (gateway['InternetGateway']['InternetGatewayId'],
                                                   vpc['Vpc']['VpcId'])
    except:
        print sys.exc_info()
    return vpc, subnet

def sec_grp_setup(ec2, vpc, prj):
    try:
        sg = ec2.create_security_group(GroupName=prj,
                    Description='Security Group for DevOps testing',
                    VpcId=vpc['Vpc']['VpcId'])
        print 'Security Group created with ID: %s' % (sg['GroupId'])

        ec2.authorize_security_group_ingress(GroupId=sg['GroupId'],
                FromPort=22, ToPort=22, CidrIp="0.0.0.0/0", IpProtocol="tcp")
        print 'Inbound Rule for Port 22 and Source 0.0.0.0/0 created'

        ec2.authorize_security_group_ingress(GroupId=sg['GroupId'],
                FromPort=80, ToPort=80, CidrIp="0.0.0.0/0", IpProtocol="tcp")
        print 'Inbound Rule for Port 80 and Source 0.0.0.0/0 created'

        ec2.authorize_security_group_ingress(GroupId=sg['GroupId'],
                FromPort=443, ToPort=443, CidrIp="0.0.0.0/0", IpProtocol="tcp")
        print 'Inbound Rule for Port 443 and Source 0.0.0.0/0 created'
    except:
        print sys.exc_info()
    return sg

def keypair_setup(ec2, prj):
    try:
        kp_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + prj + ".pem"
        kp = ec2.create_key_pair(KeyName=prj)
        if os.path.exists(kp_file):
            os.remove(kp_file)
        with open(kp_file, "w") as f:
            f.write(kp['KeyMaterial'])
        print 'KeyPair created with Name: %s' % (kp['KeyName'])
        print 'PEM file path: %s' % (kp_file)
    except:
        print sys.exc_info()
    return kp

def instance_setup(ec2, subnet, sg, kp, imgid, minc, maxc, itype):
    try:
        instance = ec2.run_instances(ImageId=imgid, MinCount=int(minc),
                      MaxCount=int(maxc), InstanceType=itype,
                      KeyName=kp['KeyName'], SecurityGroupIds=[sg['GroupId']],
                      SubnetId=subnet['Subnet']['SubnetId'])
        for inst in instance['Instances']:
            print 'Instance created with ID: %s' % (inst['InstanceId'])
    except:
        print sys.exc_info()
    return instance

def volume_setup(ec2, instance, sz, vol, dev):
    try:
        for inst in instance['Instances']:
            volume = ec2.create_volume(AvailabilityZone=inst['Placement']['AvailabilityZone'],
                     VolumeType=vol, Size=int(sz))
            print 'Volume created with ID: %s' % (volume['VolumeId'])

            print 'Waiting instance get running to attach volume...'
            time.sleep(120)

            ec2.attach_volume(InstanceId=inst['InstanceId'],
                           VolumeId=volume['VolumeId'], Device=dev)
            print 'Volume %s attached to Instance %s' % (volume['VolumeId'],
                                                         inst['InstanceId'])
    except:
        print sys.exc_info()
