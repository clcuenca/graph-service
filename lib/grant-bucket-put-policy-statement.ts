/**
 * Represents a Policy Statement that grants permission to Bucket put actions.
 * @author Carlos L. Cuenca
 */

import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Bucket } from "aws-cdk-lib/aws-s3";

/// ----------
/// Properties

export interface GrantBucketPutPolicyStatementProps {
    bucket: Bucket
}

/// -------
/// Classes

export class GrantBucketPutPolicyStatement extends PolicyStatement {

    /// -----------
    /// Constructor

    public constructor(props: GrantBucketPutPolicyStatementProps) {
        super({
            resources: [
                `${props.bucket.bucketArn}`,
                `${props.bucket.bucketArn}/*`],
            actions: ['s3:PutObject'],
            effect: Effect.ALLOW
        });
    }
}