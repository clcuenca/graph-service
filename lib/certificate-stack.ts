/**
 * Certificate Stack
 * @author Carlos L. Cuenca
 * @version 0.9.0
 */

import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import { Certificate, CertificateValidation } from 'aws-cdk-lib/aws-certificatemanager'
import { HostedZone } from 'aws-cdk-lib/aws-route53'

/// ---------------------
/// CertificateStackProps

export interface CertificateStackProps {
    account:        string,
    region:         string,
    id:             string,
    stackId:        string,
    domain:         string,
    hostedZone:     HostedZone
}

/// -------------------------------
/// CertificateStack Implementation

export class CertificateStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly _certificate: Certificate;

    /// ------------
    /// Constructors

    constructor(scope: Construct, props: CertificateStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        const wildcard = `*.${props.domain}`

        this._certificate = new Certificate(this, props.id, {
            domainName:                 props.domain,
            subjectAlternativeNames:    [wildcard],
            validation:                 CertificateValidation.fromDns(props.hostedZone)
        });

    }

    /// -------
    /// Getters

    public get certificate() {

        return this._certificate;

    }

}