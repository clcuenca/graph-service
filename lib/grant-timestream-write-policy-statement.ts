/**
 * Represents a PolicyStatement that grants permission to Table read/write actions.
 * @author Carlos L. Cuenca
 */

import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";
import { CfnDatabase } from "aws-cdk-lib/aws-timestream";

/// ----------
/// Properties

export interface GrantTimeStreamDatabaseWritePolicyStatementProps {
    database: CfnDatabase
}

/// -------
/// Classes

export class GrantTimeStreamDatabaseWritePolicyStatement extends PolicyStatement {

    /// -----------
    /// Constructor

    public constructor(props: GrantTimeStreamDatabaseWritePolicyStatementProps) {
        super({
            resources: [props.database.attrArn],
            actions: [
                "timestream:DescribeEndpoints",
                "timestream:CreateTable",
                "timestream:DescribeTable",
                "timestream:ListTables",
                "timestream:UpdateTable",
                "timestream:UpdateDatabase"
            ],
            effect: Effect.ALLOW
        });
    }
}