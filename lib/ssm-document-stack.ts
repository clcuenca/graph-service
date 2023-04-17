/**
 * Stack that contains an SSM document used by Systems Manager.
 * @author Carlos L. Cuenca
 */

import { CfnDocument } from "aws-cdk-lib/aws-ssm"
import { Stack } from 'aws-cdk-lib'
import { Construct } from 'constructs'

/// ----------
/// Properties

export interface SSMDocumentProps {
    account:        string,
    region:         string,
    stackId:        string,
    id:             string,
    name:           string,
    type:           string,
    targetType:     string,
    version:        string,
    updateMethod:   string
    content:        any,
}

/// --------------
/// Implementation

export class SSMDocumentStack extends Stack {

    private readonly _document: CfnDocument

    constructor(scope: Construct, props: SSMDocumentProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region: props.region,
            }});

        this._document = new CfnDocument(this, props.id, {
            content:        props.content,
            name:           props.name,
            documentType:   props.type,
            targetType:     props.targetType,
            updateMethod:   props.updateMethod,
            versionName:    `${props.name}${props.version}`
        });

    }

}
