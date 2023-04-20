/**
 * Stack that contains a single EC2 instance.
 * @author Carlos L. Cuenca
 * @version 1.0.0
 */
import {Construct} from 'constructs'
import {Stack} from 'aws-cdk-lib'
import {IMachineImage, Instance, InstanceType, Peer, Port, SecurityGroup, Vpc} from 'aws-cdk-lib/aws-ec2'
import {Effect, ManagedPolicy, PolicyDocument, PolicyStatement, Role, ServicePrincipal} from 'aws-cdk-lib/aws-iam'
import {Repository} from "aws-cdk-lib/aws-codecommit";
import {
    InstanceTagSet,
    ServerApplication,
    ServerDeploymentConfig,
    ServerDeploymentGroup
} from "aws-cdk-lib/aws-codedeploy";
import {
    CodeBuildAction,
    CodeCommitSourceAction,
    CodeDeployServerDeployAction
} from "aws-cdk-lib/aws-codepipeline-actions";
import {BuildSpec, LinuxBuildImage, Project} from "aws-cdk-lib/aws-codebuild";
import {Artifact} from "aws-cdk-lib/aws-codepipeline";

/// ----------
/// Properties

export interface ApplicationInstanceStackProps {
    account:            string,
    region:             string,
    stackId:            string,
    id:                 string,
    stageName:          string,
    applicationName:    string,
    keyname:            string,
    repository:         string,
    branch:             string,
    artifactName:       string,
    artifactPath:       string,
    startup:            string[],
    vpc:                Vpc,
    instanceType:       InstanceType,
    machineImage:       IMachineImage,
    policyStatements:   PolicyStatement[]
}

/// --------------
/// Implementation

export class ApplicationInstanceStack extends Stack {

    private readonly _instance:                 Instance                        ;
    private readonly _securityGroup:            SecurityGroup                   ;
    private readonly _codeBuildProject:         Project                         ;
    private readonly _repository:               Repository                      ;
    private readonly _serverApplication:        ServerApplication               ;
    private readonly _serverDeploymentGroup:    ServerDeploymentGroup           ;
    private readonly _serverCommitAction:       CodeCommitSourceAction          ;
    private readonly _serverBuildAction:        CodeBuildAction                 ;
    private readonly _serverDeployAction:       CodeDeployServerDeployAction    ;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: ApplicationInstanceStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region: props.region,
            }});

        this._securityGroup = new SecurityGroup(this, `${props.id}SecurityGroup`, {
            vpc:                props.vpc,
            allowAllOutbound:   true
        });

        this._securityGroup.addIngressRule(Peer.anyIpv4(), Port.tcp(22));
        this._securityGroup.addIngressRule(Peer.anyIpv4(), Port.tcp(80));
        this._securityGroup.addIngressRule(Peer.anyIpv4(), Port.tcp(443));

        // Initialize the EC2 instance
        this._instance = new Instance(this, props.id, {
            vpc:                props.vpc,
            instanceType:       props.instanceType,
            machineImage:       props.machineImage,
            keyName:            props.keyname,
            securityGroup:      this._securityGroup,
            role:               new Role(this, `${props.id}Role`, {
                // TODO: Maybe change to ARNPrincipal?
                assumedBy:      new ServicePrincipal('ec2.amazonaws.com'),
                inlinePolicies: {
                    'RolePolicy': new PolicyDocument({
                        statements: props.policyStatements
                    })
                },
                managedPolicies: [
                    ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore'),
                    ManagedPolicy.fromAwsManagedPolicyName('AmazonEC2RoleforAWSCodeDeploy')
                ]
            })
        });

        props.startup.forEach(command => {
            this._instance.addUserData(command)
        });

        this._codeBuildProject = new Project(this, `${props.id}CodeBuildProject`, {
            environment: {
                buildImage: LinuxBuildImage.AMAZON_LINUX_2_2,
                privileged: true
            },
            role: new Role(this, `${props.id}CodeBuildProjectRole`, {
                assumedBy:          new ServicePrincipal('codebuild.amazonaws.com'),
                inlinePolicies: {
                    accessPolicy:   new PolicyDocument({
                        statements: [
                            new PolicyStatement({
                                effect:     Effect.ALLOW,
                                resources:  ['*'],
                                actions:    ['*'],
                            })
                        ]
                    })
                }
            }),
            buildSpec: BuildSpec.fromObject({
                version: "0.1",
                phases: {
                    pre_build: {
                        commands: [],
                    },
                    build: {
                        commands: [
                            `zip ${props.artifactName}.zip ${props.artifactPath}`
                        ],
                    },
                    post_build: {
                        commands: []
                    }
                },
                artifacts: {
                    files: [
                        `${props.artifactName}.zip`,
                    ],
                }
            })
        });

        this._repository = new Repository(this, `${props.id}Repository`, {
            repositoryName: props.repository
        });

        this._serverApplication = new ServerApplication(this, `${props.id}ServerApplication`, {
            applicationName: props.applicationName
        });

        this._serverDeploymentGroup = new ServerDeploymentGroup(this, `${props.id}ServerDeploymentGroup`, {
            application:        this._serverApplication,
            deploymentConfig:   ServerDeploymentConfig.ALL_AT_ONCE,
            ec2InstanceTags:    new InstanceTagSet({
                'Name':         [`${props.stageName}/${props.stackId}/${this._instance.instanceId}`]
            }),
            role:               new Role(this, `${props.id}ServerDeploymentGroupRole`, {
                assumedBy:      new ServicePrincipal('codedeploy.amazonaws.com'),
                managedPolicies:    [ManagedPolicy.fromAwsManagedPolicyName('AWSCodeDeployRole')]
            })
        });

        const sourceOutput = new Artifact();
        const buildOutput  = new Artifact();

        this._serverCommitAction = new CodeCommitSourceAction({
            actionName:     `${props.id}SourceAction`,
            repository:     this._repository,
            branch:         props.branch,
            output:         sourceOutput
        });

        this._serverBuildAction = new CodeBuildAction({
            actionName:         `${props.id}ServerBuildAction`,
            project:            this._codeBuildProject,
            input:              sourceOutput,
            outputs:            [buildOutput]
        });

        this._serverDeployAction = new CodeDeployServerDeployAction({
            actionName:         `${props.id}ServerDeployAction`,
            deploymentGroup:    this._serverDeploymentGroup,
            input:              buildOutput
        });

    }

    get actions(): any[] {

        return [this._serverCommitAction, this._serverBuildAction, this._serverDeployAction]

    }

}