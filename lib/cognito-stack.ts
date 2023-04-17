/**
 * Cognito Stack
 * @version 0.9.0
 */

import { CfnIdentityPool, CfnIdentityPoolRoleAttachment,
    UserPool, UserPoolClient, UserPoolIdentityProviderAmazon, UserPoolTriggers, UserPoolOperation } from 'aws-cdk-lib/aws-cognito'
import {Duration, Stack} from 'aws-cdk-lib'
import { Construct } from 'constructs'
import { Role } from 'aws-cdk-lib/aws-iam'
import {AwsCustomResource, AwsCustomResourcePolicy, PhysicalResourceId} from "aws-cdk-lib/custom-resources";
import {RetentionDays} from "aws-cdk-lib/aws-logs";

/// -----------------
/// CognitoStackProps

export interface CognitoStackProps {
    account:                        string,
    region:                         string,
    id:                             string,
    stackId:                        string
}

/// ----------------------------------
/// UserPoolClientSecretRetrieverProps

export interface UserPoolClientSecretRetrieverProps {
    userPoolClientDescriptorId: string,
    userPoolId:                 string,
    userPoolClientId:           string,
    region:                     string
}

/// -----------------------------
/// UserPoolClientSecretRetriever

export class UserPoolClientSecretRetriever extends AwsCustomResource {

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: UserPoolClientSecretRetrieverProps) {
        super(scope, props.userPoolClientDescriptorId, {
            logRetention: RetentionDays.ONE_DAY,
            onCreate: {
                region:     props.region,
                service:    'CognitoIdentityServiceProvider',
                action:     'describeUserPoolClient',
                parameters: {
                    ClientId:   props.userPoolClientId,
                    UserPoolId: props.userPoolId
                },
                physicalResourceId: PhysicalResourceId.of(props.userPoolClientId)
            },
            timeout: Duration.minutes(14),
            policy:         AwsCustomResourcePolicy.fromSdkCalls({
                resources:  AwsCustomResourcePolicy.ANY_RESOURCE
            })
        });
    }

    /// ---------
    /// Accessors

    get clientSecret() {

        return this.getResponseField('UserPoolClient.ClientSecret');

    }

    get clientId() {

        return this.getResponseField('UserPoolClient.ClientId')

    }

}

/// ---------------------------
/// CognitoStack Implementation

export class CognitoStack extends Stack {

    private readonly userPool:                          UserPool                        ;
    private readonly identityPool:                      CfnIdentityPool                 ;
    private readonly userPoolClient:                    UserPoolClient                  ;
    private readonly userPoolClientSecretRetriever:     UserPoolClientSecretRetriever   ;
    private readonly userPoolIdentityProviderAmazon:    UserPoolIdentityProviderAmazon  ;

    constructor (scope: Construct, props: CognitoStackProps) {
        super(scope, props.stackId, { env: {
                account:                props.account,
                region:                 props.region
        }});

        this.userPool = new UserPool(this, `${props.id}UserPool`, {
            selfSignUpEnabled:          true,
        });

        this.userPoolClient = new UserPoolClient(this, `${props.id}UserPoolClient`, {
            userPool:                   this.userPool,
            generateSecret:             true
        });

        this.userPoolClientSecretRetriever = new UserPoolClientSecretRetriever(this, {
            userPoolClientDescriptorId: `${props.id}UserPoolClientSecretRetriever`,
            userPoolId:                 this.userPool.userPoolId,
            userPoolClientId:           this.userPoolClient.userPoolClientId,
            region:                     props.region
        });

        this.userPoolIdentityProviderAmazon = new UserPoolIdentityProviderAmazon(this, `${props.id}IdentityProvider`, {
            userPool:                   this.userPool,
            clientId:                   `${props.id}UserPoolClient`,
            clientSecret:               this.userPoolClientSecretRetriever.clientSecret
        });

        const identityProviderDomain = `cognito-idp.${Stack.of(this).region}.amazonaws.com/${this.userPool.userPoolId}:${this.userPoolClient.userPoolClientId}`

        this.identityPool = new CfnIdentityPool(this, `${props.id}IdentityPool`, {
            allowUnauthenticatedIdentities: true,
            cognitoIdentityProviders: [{
                clientId:               this.userPoolClient.userPoolClientId,
                providerName:           this.userPool.userPoolProviderName
            }]
        });

        //const authenticatedRole     = new Roles.Cognito.AuthenticatedRole(this, props.resourceArns, this.identityPool.ref).roleArn
        //const unauthenticatedRole   = new Roles.Cognito.UnauthenticatedRole(this, props.resourceArns, this.identityPool.ref).roleArn

        /*new CfnIdentityPoolRoleAttachment(
            this,
            `identity-pool-role-attachment`, {
                identityPoolId: this.identityPool.ref,
                roles: {
                    authenticated:      authenticatedRole,
                    unauthenticated:    unauthenticatedRole,
                },
                roleMappings: {
                    mapping: {
                        type: 'Token',
                        ambiguousRoleResolution: 'AuthenticatedRole',
                        identityProvider: identityProviderDomain,
                    },
                },
            },
        );

        this.userPool.addTrigger(UserPoolOperation.PRE_SIGN_UP, new Function(this, `${props.userPoolId}AutoVerifyLambda`, {
            runtime: Runtime.PYTHON_3_9,
            handler: 'cognito_pre_sign_up.handler',
            code:    Code.fromAsset('cognito_pre_sign_up.zip')
        }));*/

    }

    get userPoolId() {

        return this.userPool.userPoolId;

    }

    get identityPoolId() {

        return this.identityPool.ref;

    }

}