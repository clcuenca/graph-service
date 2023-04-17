/**
 * VPC Stack
 * @author Carlos L. Cuenca
 * @version 0.1.0
 */

import { Construct } from 'constructs'
import { Stack, Stage } from 'aws-cdk-lib'
import { Vpc, SubnetConfiguration, SubnetType } from 'aws-cdk-lib/aws-ec2'

/// -------------
/// VpcStackProps

export interface VpcStackProps {
    account:                string,
    region:                 string,
    id:                     string,
    stackId:                string,
    cidr:                   string,
    maxAzs:                 number,
    natGateways:            number,
    subnetConfiguration:    SubnetConfiguration[],
    enableDnsHostnames:     boolean,
    enableDnsSupport:       boolean
}

/// -----------------------
/// VpcStack Implementation

export class VpcStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly _vpc: Vpc;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: VpcStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this._vpc = new Vpc(this, props.id, {
            cidr:                 props.cidr,
            maxAzs:               props.maxAzs,
            natGateways:          props.natGateways,
            enableDnsHostnames:   props.enableDnsHostnames,
            enableDnsSupport:     props.enableDnsSupport,
            subnetConfiguration:  props.subnetConfiguration
        });

    }

    /// -------
    /// Getters

    public get vpc() {

        return this._vpc;

    }

    public get privateNatSubnets() {

        return this._vpc.selectSubnets({
            subnetType: SubnetType.PRIVATE_WITH_NAT
        });

    }

    public get privateIsolatedSubnets() {

        return this._vpc.selectSubnets({
            subnetType: SubnetType.PRIVATE_ISOLATED
        });

    }

    public get publicSubnets() {

        return this._vpc.selectSubnets({
            subnetType: SubnetType.PUBLIC
        });

    }

}