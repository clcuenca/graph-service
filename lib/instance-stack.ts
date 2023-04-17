/**
 * Stack that contains a single EC2 instance.
 * @author Carlos L. Cuenca
 * @version 1.0.0
 */
import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import {
    Instance,
    InstanceType,
    IMachineImage,
    Vpc,
    CfnInstance,
    SecurityGroup,
    Port,
    Peer
} from 'aws-cdk-lib/aws-ec2'
import {ManagedPolicy, PolicyDocument, PolicyStatement, Role, ServicePrincipal, User} from 'aws-cdk-lib/aws-iam'

/// ----------
/// Properties

export interface InstanceProps {
    account:            string,
    region:             string,
    stackId:            string,
    id:                 string,
    instanceType:       InstanceType,
    machineImage:       IMachineImage,
    policyStatements:   PolicyStatement[],
    keyname:            string,
    startup:            string[]
}

/// --------------
/// Implementation

export class InstanceStack extends Stack {

    private readonly _instance: Instance;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: InstanceProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region: props.region,
            }});

        const defaultVPC = Vpc.fromLookup(this, `${props.stackId}Vpc`, {
            isDefault: true
        });

        const securityGroup = new SecurityGroup(this, `${props.id}SecurityGroup`, {
            vpc: defaultVPC,
            allowAllOutbound: true
        });

        securityGroup.addIngressRule(Peer.anyIpv4(), Port.tcp(22));
        securityGroup.addIngressRule(Peer.anyIpv4(), Port.tcp(80));
        securityGroup.addIngressRule(Peer.anyIpv4(), Port.tcp(443));

        // Assign the default vpc
        this._instance = new Instance(this, props.id, {
            vpc         :       defaultVPC,
            instanceType:       props.instanceType,
            machineImage:       props.machineImage,
            securityGroup:      securityGroup,
            keyName:            props.keyname,
            role:               new Role(this, `${props.id}Role`, {
                // TODO: Maybe change to ARNPrincipal?
                assumedBy:      new ServicePrincipal('ec2.amazonaws.com'),
                inlinePolicies: {
                    'RolePolicy': new PolicyDocument({
                        statements: props.policyStatements
                    })
                },
                managedPolicies: [
                    ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore')
                ]
            })
        });

        props.startup.forEach(command => {
            this._instance.addUserData(command)
        });

    }

}