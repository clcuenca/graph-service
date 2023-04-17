/**
 * Cognito Stack
 * @version 0.9.0
 */

import { CfnIdentityPool, CfnIdentityPoolRoleAttachment,
    UserPool, UserPoolClient, UserPoolIdentityProviderAmazon, UserPoolTriggers, UserPoolOperation } from 'aws-cdk-lib/aws-cognito'
import { Stack } from 'aws-cdk-lib'
import { Construct } from 'constructs'
import { Role } from 'aws-cdk-lib/aws-iam'
import { Secret } from 'aws-cdk-lib/aws-secretsmanager'
import { Function, Runtime, Code } from 'aws-cdk-lib/aws-lambda'
import { Constants } from './constants'

/// -----------------
/// CognitoStackProps

export interface CognitoStackProps {
    account:                        string,
    region:                         string,
    id:                             string,
    stackId:                        string,
    userPoolId:                     string,
    identityPoolId:                 string,
    identityProviderId:             string,
    userPoolClientId:               string,
    selfSignUpEnabled:              boolean,
    autoVerifyEmail:                boolean,
    enableAliasUsername:            boolean,
    enableAliasEmail:               boolean,
    fullnameRequired:               boolean,
    fullnameMutable:                boolean,
    emailRequired:                  boolean,
    emailMutable:                   boolean,
    passwordMinimumLength:          number,
    allowUnauthenticatedIdentities: boolean,
    resourceArns:                   string[]
}

/// ---------------------------
/// CognitoStack Implementation

export class CognitoStack extends Stack {

    private readonly userPool:                          UserPool
    private readonly identityPool:                      CfnIdentityPool
    private readonly userPoolClient:                    UserPoolClient
    private readonly userPoolIdentityProviderAmazon:    UserPoolIdentityProviderAmazon

    constructor (scope: Construct, props: CognitoStackProps) {
        super(scope, props.stackId, { env: {
                account:    props.account,
                region:     props. region
            }});

        this.userPool = new UserPool(this, props.userPoolId, {
            selfSignUpEnabled:          props.selfSignUpEnabled,
            autoVerify: {
                email:                  props.autoVerifyEmail
            },
            signInAliases: {
                username:               props.enableAliasUsername,
                email:                  props.enableAliasEmail
            },
            standardAttributes: {
                fullname: {
                    required:           props.fullnameRequired,
                    mutable:            props.fullnameMutable
                },
                /*                 email: {
                                    required:           props.emailRequired,
                                    mutable:            props.emailMutable
                                } */
            },
            passwordPolicy: {
                minLength:              props.passwordMinimumLength,
            },
        });

        this.userPoolClient = new UserPoolClient(this, props.userPoolClientId, {
            userPool: this.userPool
        });

        /*this.userPoolIdentityProviderAmazon = new UserPoolIdentityProviderAmazon(this, props.identityProviderId, {
            userPool:       this.userPool,
            clientId:       props.userPoolClientId,
            clientSecret:   Secret.fromSecretAttributes(this, `${props.id}IdentityProviderSecret`, {
                secretCompleteArn: Constants.Cognito.IdentityProviderSecretArn
            }).secretValue.unsafeUnwrap()
        });*/

        const identityProviderDomain = `cognito-idp.${Stack.of(this).region}.amazonaws.com/${this.userPool.userPoolId}:${this.userPoolClient.userPoolClientId}`

        this.identityPool = new CfnIdentityPool(this, props.identityPoolId, {
            allowUnauthenticatedIdentities: props.allowUnauthenticatedIdentities,
            cognitoIdentityProviders: [{
                clientId:       this.userPoolClient.userPoolClientId,
                providerName:   this.userPool.userPoolProviderName

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

}