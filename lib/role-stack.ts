/**
 * Stack that defines an IAM role
 * @author Carlos L. Cuenca
 * @version 1.0.0
 */

import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import { PolicyDocument, PrincipalBase, Role } from 'aws-cdk-lib/aws-iam'

/// ----------
/// Properties

export interface RoleStackProps {
    account:            string,
    region:             string,
    stackId:            string,
    id:                 string,
    principal:          PrincipalBase,
    inlinePolicies:     { [p: string]: PolicyDocument } | undefined
}

/// --------------------
/// Class Implementation

export class RoleStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly _role: Role    ;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: RoleStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this._role = new Role(this, props.id, {
            assumedBy:      props.principal,
            inlinePolicies: props.inlinePolicies
        });

    }

    /// -------
    /// Getters

    get role() {

        return this._role;

    }

}
