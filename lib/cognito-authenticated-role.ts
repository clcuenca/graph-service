/**
 * Represents an OpenSearch Cognito Access Role.
 * @author Carlos L. Cuenca
 * @version 0.9.0
 */
import {Effect, FederatedPrincipal, ManagedPolicy, PolicyStatement, Role, ServicePrincipal} from "aws-cdk-lib/aws-iam";
import {Construct} from "constructs";

/// ----------
/// Properties

export interface CognitoAuthenticatedRoleProps {
    id:             string,
    identityPoolId: string,
    arns:           string[]
}

export class CognitoAuthenticatedRole extends Role {

    /// -----------
    /// Constructor

    public constructor(scope: Construct, props: CognitoAuthenticatedRoleProps) {
        super(scope, props.id, {
            assumedBy: new FederatedPrincipal('cognito-identity.amazonaws.com', {
                StringEquals: {
                    'cognito-identity.amazonaws.com:aud': props.identityPoolId
                },
                'ForAnyValue:StringLike': {
                    'cognito-identity.amazonaws.com:amr': 'authenticated'
                }
            },'sts:AssumeRoleWithWebIdentity')
        });

        // Necessary Trust Policy;
        this.addToPolicy(new PolicyStatement({
            effect:     Effect.ALLOW,
            actions:    ['es:ESHttp*'],
            resources:  props.arns
        }));

    }

}