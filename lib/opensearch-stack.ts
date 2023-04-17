/**
 * OpenSearch Service
 * @author Carlos L. Cuenca
 * @version 0.9.0
 */

import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import {Domain, EngineVersion} from 'aws-cdk-lib/aws-opensearchservice'
import {CnameRecord, HostedZone} from "aws-cdk-lib/aws-route53";
import {Certificate} from "aws-cdk-lib/aws-certificatemanager";
import {OpensearchCognitoAccessRole} from "./opensearch-cognito-access-role";
import {CognitoAuthenticatedRole} from "./cognito-authenticated-role";
import {CognitoUnauthenticatedRole} from "./cognito-unauthenticated-role";
import {CfnIdentityPoolRoleAttachment} from "aws-cdk-lib/aws-cognito";

/// --------------------
/// HostedZoneStackProps

export interface OpenSearchStackProps {
    account:                string,
    region:                 string,
    id:                     string,
    stackId:                string,
    identityPoolId:         string,
    userPoolId:             string,
    domainName:             string,
    identityProviderDomain: string,
    hostedZone:             HostedZone,
    certificate:            Certificate
}

/// ------------------------------
/// HostedZoneStack Implementation

export class OpenSearchStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly _domain:                       Domain                          ;
    private readonly _cnameRecord:                  CnameRecord                     ;
    private readonly _cognitoAuthenticatedRole:     CognitoAuthenticatedRole        ;
    private readonly _cognitoUnauthenticatedRole:   CognitoUnauthenticatedRole      ;
    private readonly _identityPoolRoleAttachement:  CfnIdentityPoolRoleAttachment   ;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: OpenSearchStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this._domain = new Domain(this, `${props.id}Domain`, {
            version:                EngineVersion.OPENSEARCH_1_0,
            enableVersionUpgrade:   true,
            enforceHttps:           true,
            nodeToNodeEncryption:   true,
            encryptionAtRest: {
                enabled: true
            },
            cognitoDashboardsAuth: {
                userPoolId:         props.userPoolId,
                identityPoolId:     props.identityPoolId,
                role:               new OpensearchCognitoAccessRole(this, {
                    id:             `${props.id}AccessRole`,
                    arns:            ['*'] // TODO: Check if this is necessary; There's something in the docs about this
                })
            },
            customEndpoint: {
                domainName:         props.domainName,
                hostedZone:         props.hostedZone,
                certificate:        props.certificate
            }
        });

        this._cnameRecord = new CnameRecord(this, `${props.id}CNAMERecord`, {
            recordName: props.domainName.toLowerCase(),
            zone:       props.hostedZone,
            domainName: this._domain.domainEndpoint
        });

        this._cognitoAuthenticatedRole = new CognitoAuthenticatedRole(this, {
            id:             `${props.id}CognitoAuthenticatedRole`,
            identityPoolId: props.identityPoolId,
            arns:           [`${this._domain.domainArn}/*`]
        });

        this._cognitoUnauthenticatedRole = new CognitoUnauthenticatedRole(this, {
            id:             `${props.id}CognitoUnauthenticatedRole`,
            identityPoolId: props.identityPoolId,
            arns:           [`${this._domain.domainArn}/*`]
        });

        this._identityPoolRoleAttachement = new CfnIdentityPoolRoleAttachment(this,
            `${props.id}IdentityPoolRoleAttachement`, {
                identityPoolId: props.identityPoolId,
                roles: {
                    authenticated:      this._cognitoAuthenticatedRole.roleArn,
                    unauthenticated:    this._cognitoUnauthenticatedRole.roleArn
                },
                roleMappings: {
                    mapping: {
                        type:                       'Token',
                        ambiguousRoleResolution:    'AuthenticatedRole',
                        identityProvider:           props.identityProviderDomain,
                    },
                },

        });

    }

}