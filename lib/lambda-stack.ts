/**
 * Lambda stack
 * @author Carlos L. Cuenca
 * @version 1.0.0
 */

import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import { Code, Function, Runtime } from 'aws-cdk-lib/aws-lambda'
import { Role } from 'aws-cdk-lib/aws-iam'
import { Duration } from 'aws-cdk-lib'

/// ----------
/// Properties

export interface LambdaStackProps {
    account:        string,
    region:         string,
    stackId:        string,
    lambdaId:       string,
    handler:        string,
    runtime:        Runtime,
    codePath:       string,
    retryAttempts:  number,
    timeoutMinutes: number,
    role:           Role
}

/// --------------------
/// Class Implementation

export class LambdaStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly _lambda: Function;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: LambdaStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this._lambda = new Function(this, props.lambdaId, {
            runtime:        props.runtime,
            handler:        props.handler,
            retryAttempts:  props.retryAttempts,
            role:           props.role,
            code:           Code.fromAsset(props.codePath),
            timeout:        Duration.minutes(props.timeoutMinutes)
        });

    }

    get handler() {

        return this._lambda;

    }

}
