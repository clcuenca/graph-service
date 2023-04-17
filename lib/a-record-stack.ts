/**
 * A Record Stack implementation
 * @author Carlos L. Cuenca
 * @version 0.9.0
 */

import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import { ARecord, HostedZone, RecordTarget } from 'aws-cdk-lib/aws-route53'

/// -----------------
/// ARecordStackProps

export interface ARecordStackProps {
    account:        string,
    region:         string,
    id:             string,
    stackId:        string,
    domain:         string,
    hostedZone:     HostedZone,
    recordTarget:   RecordTarget
}

/// ---------------------------
/// ARecordStack Implementation

export class ARecordStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly record: ARecord;

    /// ------------
    /// Constructors

    constructor(scope: Construct, props: ARecordStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this.record = new ARecord(this, props.id, {
            zone:       props.hostedZone,
            recordName: props.domain,
            target:     props.recordTarget
        });

    }

}