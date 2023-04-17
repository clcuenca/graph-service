/**
 * Represents a PolicyStatement that grants permission to Table read/write actions.
 * @author Carlos L. Cuenca
 */

import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Table } from "aws-cdk-lib/aws-dynamodb";

/// ----------
/// Properties

export interface GrantTableReadWritePolicyStatementProps {
    table: Table
}

/// -------
/// Classes

export class GrantTableReadWritePolicyStatement extends PolicyStatement {

    /// -----------
    /// Constructor

    public constructor(props: GrantTableReadWritePolicyStatementProps) {
        super({
            resources: [props.table.tableArn],
            actions: [
                'dynamodb:GetItem',
                'dynamodb:PutItem'
            ],
            effect: Effect.ALLOW
        });
    }
}