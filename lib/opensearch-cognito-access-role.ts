/**
 * Represents an OpenSearch Cognito Access Role.
 * @author Carlos L. Cuenca
 * @version 0.9.0
 */
import {Effect, ManagedPolicy, PolicyStatement, Role, ServicePrincipal} from "aws-cdk-lib/aws-iam";
import {Construct} from "constructs";

/// ----------
/// Properties

export interface OpensearchCognitoAccessRoleProps {
    id:     string,
    arns:   string[]
}

export class OpensearchCognitoAccessRole extends Role {

    /// -----------
    /// Constructor

    public constructor(scope: Construct, props: OpensearchCognitoAccessRoleProps) {
        super(scope, props.id, {
            // Or es.amazonaws.com?
            assumedBy: new ServicePrincipal('opensearchservice.amazonaws.com'),
            // Attach the Managed Role; necessary for OpenSearch to communicate with Cognito
            managedPolicies:    [ManagedPolicy.fromAwsManagedPolicyName('AmazonOpenSearchServiceCognitoAccess')]
        });

        // Necessary Trust Policy; The wildcard is needed per the doc? (Need to find this)
        this.addToPolicy(new PolicyStatement({
            effect:     Effect.ALLOW,
            actions:    ['sts:AssumeRole'],
            resources:  props.arns
        }));

    }

}