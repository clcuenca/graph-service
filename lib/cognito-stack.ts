/**
 * Cognito Stack
 * @version 0.9.0
 */

import { CfnIdentityPool, UserPool, UserPoolClient, UserPoolIdentityProviderAmazon } from 'aws-cdk-lib/aws-cognito'
import { Duration, Stack } from 'aws-cdk-lib'
import { Construct } from 'constructs'
import { AwsCustomResource, AwsCustomResourcePolicy, PhysicalResourceId } from "aws-cdk-lib/custom-resources";
import { RetentionDays } from "aws-cdk-lib/aws-logs";

/// -----------------
/// CognitoStackProps

export interface CognitoStackProps {
    account:                        string,
    region:                         string,
    id:                             string,
    stackId:                        string,
    prefix:                         string
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
    private readonly _identityProviderDomain:           string                          ;

    constructor (scope: Construct, props: CognitoStackProps) {
        super(scope, props.stackId, { env: {
                account:                props.account,
                region:                 props.region
        }});

        this.userPool = new UserPool(this, `${props.id}UserPool`, {
            selfSignUpEnabled:          true,
        });

        this.userPool.addDomain(`${props.id}${props.prefix}Domain`, {
            cognitoDomain: {
                domainPrefix: `unlv-cs-789-${props.prefix}`
            }
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

        this._identityProviderDomain = `cognito-idp.${Stack.of(this).region}.amazonaws.com/${this.userPool.userPoolId}:${this.userPoolClient.userPoolClientId}`

        this.identityPool = new CfnIdentityPool(this, `${props.id}IdentityPool`, {
            allowUnauthenticatedIdentities: true,
            cognitoIdentityProviders: [{
                clientId:               this.userPoolClient.userPoolClientId,
                providerName:           this.userPool.userPoolProviderName
            }]
        });

    }

    get identityProviderDomain() {

        return this._identityProviderDomain;

    }

    get identityPoolId() {

        return this.identityPool.ref;

    }

    get userPoolId() {

        return this.userPool.userPoolId;

    }

}