/**
 * Hosted Zone Stack
 * @author Carlos L. Cuenca
 * @version 0.9.0
 */

import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import { HostedZone } from 'aws-cdk-lib/aws-route53'

/// --------------------
/// HostedZoneStackProps

export interface HostedZoneStackProps {
    account:    string,
    region:     string,
    id:         string,
    stackId:    string,
    domainName: string
}

/// ------------------------------
/// HostedZoneStack Implementation

export class HostedZoneStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly _hostedZone: HostedZone  ;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: HostedZoneStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this._hostedZone = HostedZone.fromLookup(this, props.id, {
            domainName: props.domainName
        }) as HostedZone;
    }

    /// -------
    /// Getters

    public get hostedZone() {

        return this._hostedZone;

    }

}