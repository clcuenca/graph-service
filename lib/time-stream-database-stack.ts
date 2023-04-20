/**
 * Stack that contains a TimeStream Database
 * @author Carlos L. Cuenca
 */
import {Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {InstanceProps} from "./instance-stack";
import {CfnDatabase} from "aws-cdk-lib/aws-timestream";

/// ----------
/// Properties

export interface TimeStreamDatabaseStackProps {
    account:            string,
    region:             string,
    stackId:            string,
    id:                 string,
}

export class TimeStreamDatabaseStack extends Stack {

    private readonly _database: CfnDatabase;

    constructor(scope: Construct, props: TimeStreamDatabaseStackProps) {
        super(scope, props.stackId, {
            env: {
                account: props.account,
                region: props.region,
            }
        });

        this._database = new CfnDatabase(this, `${props.id}Database`, {
            databaseName: props.id,
        });

    }

    get database(): CfnDatabase {

        return this._database;

    }

}