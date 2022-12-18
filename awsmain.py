# -*- coding: utf-8 -*-

import ConfigParser
import argparse
import os
import sys
import awsopers as aws

config = ConfigParser.ConfigParser()
default_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + "aws.ini"

parser = argparse.ArgumentParser(description='Automate AWS instances creation')
parser.add_argument("--config", "-c", help='Path of the config file.',
                    default=default_file)

if __name__ == "__main__":
    print "AUTOMATE AWS"
    print "=" * 20

    # Verifica o argumento e se o arquivo de configuracao existe
    args = parser.parse_args()
    if os.path.exists(args.config):
        config.read(args.config)
    else:
        print "Config file %s not found" % (args.config)

    # Converte o arquivo de configuracao em um dicionario,
    # para melhor manipulacao
    optdict = {}
    for s in config.sections():
        for o in config.options(s):
            optdict[o] = config.get(s,o)

    ec2 = aws.connect(optdict['region_name'])
    vpc, subnet = aws.vpc_setup(ec2, optdict['vpc_cidr_block'], optdict['subnet_cidr_block'])
    sg = aws.sec_grp_setup(ec2, vpc, optdict['project_name'])
    kp = aws.keypair_setup(ec2, optdict['project_name'])
    instance = aws.instance_setup(ec2, subnet, sg, kp, optdict['ami_image'],
               optdict['min_count'], optdict['max_count'], optdict['machine_size'])
    aws.volume_setup(ec2, instance, optdict['disk_storage_gb'], optdict['disk_type'],
                    optdict['device'])

    sys.exit(0)
