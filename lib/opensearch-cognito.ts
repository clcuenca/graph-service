/**
 * OpenSearch Service
 * @author Carlos L. Cuenca
 * @version 0.9.0
 */

import {Construct} from 'constructs'
import {Duration, RemovalPolicy, Stack} from 'aws-cdk-lib'
import {Domain, EngineVersion} from 'aws-cdk-lib/aws-opensearchservice'
import {CnameRecord, HostedZone} from "aws-cdk-lib/aws-route53";
import {Certificate, CertificateValidation} from "aws-cdk-lib/aws-certificatemanager";
import {OpensearchCognitoAccessRole} from "./opensearch-cognito-access-role";
import {CognitoAuthenticatedRole} from "./cognito-authenticated-role";
import {CognitoUnauthenticatedRole} from "./cognito-unauthenticated-role";
import {
    CfnIdentityPool,
    CfnIdentityPoolRoleAttachment,
    UserPool,
    UserPoolClient,
    UserPoolDomain,
    UserPoolIdentityProviderAmazon
} from "aws-cdk-lib/aws-cognito";
import {AwsCustomResource, AwsCustomResourcePolicy, PhysicalResourceId} from "aws-cdk-lib/custom-resources";
import {RetentionDays} from "aws-cdk-lib/aws-logs";

/// ----------------------------------
/// UserPoolClientSecretRetrieverProps

interface UserPoolClientSecretRetrieverProps {
    userPoolClientDescriptorId: string,
    userPoolId:                 string,
    userPoolClientId:           string,
    region:                     string
}

/// -----------------------------
/// UserPoolClientSecretRetriever

class UserPoolClientSecretRetriever extends AwsCustomResource {

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

/// --------------------
/// HostedZoneStackProps

export interface OpenSearchCognitoStackProps {
    account:                string,
    region:                 string,
    id:                     string,
    stackId:                string,
    domainName:             string,
    stage:                  string
}

/// ------------------------------
/// HostedZoneStack Implementation

export class OpenSearchCognitoStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly _hostedZone:                       HostedZone                      ;
    private readonly _certificate:                      Certificate                     ;
    private readonly _domain:                           Domain                          ;
    private readonly _cnameRecord:                      CnameRecord                     ;
    private readonly _cognitoAuthenticatedRole:         CognitoAuthenticatedRole        ;
    private readonly _cognitoUnauthenticatedRole:       CognitoUnauthenticatedRole      ;
    private readonly _identityPoolRoleAttachment:       CfnIdentityPoolRoleAttachment   ;
    private readonly _userPool:                         UserPool                        ;
    private readonly _userPoolDomain:                   UserPoolDomain                  ;
    private readonly identityPool:                      CfnIdentityPool                 ;
    private readonly userPoolClient:                    UserPoolClient                  ;
    private readonly userPoolClientSecretRetriever:     UserPoolClientSecretRetriever   ;
    private readonly userPoolIdentityProviderAmazon:    UserPoolIdentityProviderAmazon  ;
    private readonly _identityProviderDomain:           string                          ;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: OpenSearchCognitoStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this._userPool = new UserPool(this, `${props.id}UserPool`, {
            selfSignUpEnabled:          true, // TODO: Do we need this?
            removalPolicy:              RemovalPolicy.DESTROY // TODO: What is this for?
        });

        this._userPoolDomain = new UserPoolDomain(this, `${props.id}UserPoolDomain`, {
            userPool:                   this._userPool,
            cognitoDomain: {
                domainPrefix:           `${props.id.toLowerCase()}-unlv-cs-789`
            }
        });

        this.userPoolClient = new UserPoolClient(this, `${props.id}UserPoolClient`, {
            userPool:                   this._userPool,
            generateSecret:             true
        });

        this.userPoolClientSecretRetriever = new UserPoolClientSecretRetriever(this, {
            userPoolClientDescriptorId: `${props.id}UserPoolClientSecretRetriever`,
            userPoolId:                 this._userPool.userPoolId,
            userPoolClientId:           this.userPoolClient.userPoolClientId,
            region:                     props.region
        });

        this.userPoolIdentityProviderAmazon = new UserPoolIdentityProviderAmazon(this, `${props.id}IdentityProvider`, {
            userPool:                   this._userPool,
            clientId:                   `${props.id}UserPoolClient`,
            clientSecret:               this.userPoolClientSecretRetriever.clientSecret
        });

        this._identityProviderDomain = `cognito-idp.${Stack.of(this).region}.amazonaws.com/${this._userPool.userPoolId}:${this.userPoolClient.userPoolClientId}`

        this.identityPool = new CfnIdentityPool(this, `${props.id}IdentityPool`, {
            allowUnauthenticatedIdentities: true,
            cognitoIdentityProviders: [{
                clientId:               this.userPoolClient.userPoolClientId,
                providerName:           this._userPool.userPoolProviderName
            }]
        });

        this._hostedZone = HostedZone.fromLookup(this, `${props.id}HostedZone`, {
            domainName: props.domainName
        }) as HostedZone;

        this._certificate = new Certificate(this, `${props.id}HostedZoneCertificate`, {
            domainName:                 props.domainName,
            subjectAlternativeNames:    [`*.${props.domainName}`],
            validation:                 CertificateValidation.fromDns(this._hostedZone)
        });

        const openSearchAccessRole = new OpensearchCognitoAccessRole(this, {
            id: `${props.id}AccessRole`,
            arns: ['*'] // TODO: Check if this is necessary; there's something in the docs about this
        });

        this._domain = new Domain(this, `${props.id}Domain`, {
            version:                EngineVersion.OPENSEARCH_1_0,
            enableVersionUpgrade:   true,
            enforceHttps:           true,
            nodeToNodeEncryption:   true,
            encryptionAtRest: {
                enabled: true
            },
            cognitoDashboardsAuth: {
                userPoolId:         this._userPool.userPoolId,
                identityPoolId:     this.identityPool.ref,
                role:               openSearchAccessRole
            },
            customEndpoint: {
                domainName:         `${props.stage}.${props.domainName}`,
                hostedZone:         this._hostedZone,
                certificate:        this._certificate
            }
        });// Test

        //this._cnameRecord = new CnameRecord(this, `${props.id}CNAMERecord`, {
        //    recordName: `alpha.${props.domainName.toLowerCase()}`,
        //    zone:       this._hostedZone,
        //    domainName: this._domain.domainEndpoint
        //});

        this._cognitoAuthenticatedRole = new CognitoAuthenticatedRole(this, {
            id:             `${props.id}CognitoAuthenticatedRole`,
            identityPoolId: this.identityPool.ref,
            arns:           [`${this._domain.domainArn}/*`]
        });

        this._cognitoUnauthenticatedRole = new CognitoUnauthenticatedRole(this, {
            id:             `${props.id}CognitoUnauthenticatedRole`,
            identityPoolId: this.identityPool.ref,
            arns:           [`${this._domain.domainArn}/*`]
        });

        this._identityPoolRoleAttachment = new CfnIdentityPoolRoleAttachment(this,
            `${props.id}IdentityPoolRoleAttachement`, {
                identityPoolId:         this.identityPool.ref,
                roles: {
                    authenticated:      this._cognitoAuthenticatedRole.roleArn,
                    unauthenticated:    this._cognitoUnauthenticatedRole.roleArn
                },
                roleMappings: {
                    mapping: {
                        type:                       'Token',
                        ambiguousRoleResolution:    'AuthenticatedRole',
                        identityProvider:           this._identityProviderDomain,
                    },

                },

            });

    }

}