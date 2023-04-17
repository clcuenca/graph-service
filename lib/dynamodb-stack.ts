/**
 * Stack that contains a single DynamoDB table.
 * @author Carlos L. Cuenca
 */

import { Attribute, Table } from 'aws-cdk-lib/aws-dynamodb'
import { Stack } from 'aws-cdk-lib'
import { Construct } from 'constructs'

/// ----------
/// Properties

export interface TableProps {
    partitionKey: Attribute,
    tableName:    string,
    stackId:      string,
    id:           string,
    accountId:    string,
    region:       string,
}

/// --------------
/// Implementation

export class DynamoDBStack extends Stack {

    /// --------------
    /// Private Fields

    private readonly _db: Table;

    /// -----------
    /// Constructor

    public constructor(scope: Construct, props: TableProps) {
        super(scope, props.stackId, { env: {
                account: props.accountId,
                region: props.region,
            }});

        this._db = new Table(this, props.id, {
            partitionKey:   props.partitionKey,
            tableName:      props.tableName
        });

    }

    get table(): Table {

        return this._db;

    }

}
