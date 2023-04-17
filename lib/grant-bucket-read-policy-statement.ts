/**
 * Represents a PolicyStatement that grants permission to Bucket read actions
 * @author Carlos L. Cuenca
 */

import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Bucket } from "aws-cdk-lib/aws-s3";

/// ----------
/// Properties

export interface GrantBucketReadPolicyStatementProps {
    bucket: Bucket
}

/// -------
/// Classes

export class GrantBucketReadPolicyStatement extends PolicyStatement {

    /// -----------
    /// Constructor

    public constructor(props: GrantBucketReadPolicyStatementProps) {
        super({
            resources: [`${props.bucket.bucketArn}/*`],
            actions: ['s3:GetObject'],
            effect: Effect.ALLOW
        });
    }
}