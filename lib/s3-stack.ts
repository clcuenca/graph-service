/**
 * Stack that contains a single S3 bucket.
 */

import { Construct } from 'constructs'
import { Stack } from 'aws-cdk-lib'
import { Bucket } from 'aws-cdk-lib/aws-s3'

/// ----------
/// Properties

export interface S3Props {
    account:      string,
    region:       string,
    stackId:      string,
    bucketName:   string,
    id:           string,
}

/// --------------
/// Implementation

export class S3Stack extends Stack {


    private readonly _s3: Bucket;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: S3Props) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region: props.region,
            }});

        this._s3 = new Bucket(this, props.id, {
            bucketName: props.bucketName,
        });

    }

    get bucket(): Bucket {

        return this._s3;

    }

}