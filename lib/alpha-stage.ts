/**
 * Alpha Stage
 * @author Kirsten Tan
 * @author Carlos L. Cuenca
 * @version 0.1.0
 */

import { Construct } from 'constructs'
import { Stage } from 'aws-cdk-lib'
import { AttributeType } from "aws-cdk-lib/aws-dynamodb";
import { IMachineImage, InstanceType } from "aws-cdk-lib/aws-ec2";
import { S3Stack } from "./s3-stack";
import { DynamoDBStack } from "./dynamodb-stack";
import { InstanceStack } from "./instance-stack";
import { SSMDocumentStack} from "./ssm-document-stack";
import { GrantBucketReadPolicyStatement } from "./grant-bucket-read-policy-statement";
import { GrantBucketPutPolicyStatement } from "./grant-bucket-put-policy-statement";
import { GrantTableReadWritePolicyStatement } from "./grant-table-read-write-policy-statement";
import {HostedZoneStack} from "./hosted-zone-stack";
import {CertificateStack} from "./certificate-stack";
import {CognitoStack} from "./cognito-stack";
import {OpenSearchStack} from "./opensearch-stack";
import {HostedZone} from "aws-cdk-lib/aws-route53";
import {Certificate} from "aws-cdk-lib/aws-certificatemanager";
import {OpenSearchCognitoStack} from "./opensearch-cognito";

/// -----------------
/// Alpha Stage Props

export interface AlphaStageProps {
    account:                    string,
    region:                     string,
    stageId:                    string,
    stageName:                  string,
    appName:                    string,
    ec2ServicePrincipal:        string,
    mlTrainingInstanceType:     InstanceType,
    mlTrainingMachineImage:     IMachineImage,
    mlTrainingKeyPairName:      string,
    mlTrainingStartup:          string[],
    ingestionInstanceType:      InstanceType,
    ingestionMachineImage:      IMachineImage,
    ingestionKeyPairName:       string,
    ingestionStartup:           string[],
    algorithmicInstanceType:    InstanceType,
    algorithmicMachineImage:    IMachineImage,
    algorithmicKeyPairName:     string,
    algorithmicStartup:         string[],
    trainingSSMDocument:        any,
    opensearchDomain:           string
}

/// --------------------------
/// Alpha Stage Implementation

export class AlphaStage extends Stage {

    /// ---------------
    /// Private Members

    private readonly datasetsBucket:                S3Stack                 ;
    private readonly ingestionScriptsBucket:        S3Stack                 ;
    private readonly mlScriptsBucket:               S3Stack                 ;
    private readonly mlDatasetsBucket:              S3Stack                 ;
    private readonly mlModelsBucket:                S3Stack                 ;
    private readonly modelsTableStack:              DynamoDBStack           ;
    private readonly ingestionTableStack:           DynamoDBStack           ;
    private readonly trainingSSMDocumentStack:      SSMDocumentStack        ;
    private readonly mlTrainingInstanceStack:       InstanceStack           ;
    private readonly ingestionInstanceStack:        InstanceStack           ;
    private readonly algorithmicInstanceStack:      InstanceStack           ;
    private readonly opensearchStack:               OpenSearchCognitoStack  ;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: AlphaStageProps) {
        super(scope, props.stageId, { env: {
                account:        props.account,
                region:         props.region
            }});

        this.opensearchStack = new OpenSearchCognitoStack(this, {
            account:                props.account,
            region:                 props.region,
            id:                     `${props.appName}OpenSearch`,
            stackId:                `${props.appName}OpenSearchStack`,
            domainName:             props.opensearchDomain,
            stage:                  'alpha'
        });

        this.datasetsBucket = new S3Stack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}DatasetsBucketStack`,
            id:                 `${props.appName}DatasetsBucket`,
            bucketName:         `${props.appName}-datasets-bucket`
        });

        this.ingestionScriptsBucket = new S3Stack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}IngestionScriptsBucketStack`,
            id:                 `${props.appName}IngestionScriptsBucket`,
            bucketName:         `${props.appName}-ingestion-scripts-bucket`
        });

        this.mlDatasetsBucket = new S3Stack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}MLDatasetsBucketStack`,
            id:                 `${props.appName}MLDatasetsBucket`,
            bucketName:         `${props.appName}-ml-datasets-bucket`
        });

        this.mlModelsBucket = new S3Stack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}MLModelsBucketStack`,
            id:                 `${props.appName}MLModelsBucket`,
            bucketName:         `${props.appName}-ml-models-bucket`
        });

        this.mlScriptsBucket = new S3Stack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}MLScriptsBucketStack`,
            id:                 `${props.appName}MLScriptsBucket`,
            bucketName:         `${props.appName}-ml-scripts-bucket`
        });

        this.ingestionTableStack = new DynamoDBStack(this, {
            accountId:          props.account,
            region:             props.region,
            stackId:            `${props.appName}ParlerIngestionTableStack`,
            id:                 `${props.appName}ParlerIngestionTable`,
            tableName:          `${props.appName}ParlerIngestionTable`,
            partitionKey:       { name: 'id', type: AttributeType.STRING }
        });

        this.modelsTableStack = new DynamoDBStack(this, {
            accountId:          props.account,
            region:             props.region,
            stackId:            `${props.appName}ModelsTableStack`,
            id:                 `${props.appName}ModelsTable`,
            tableName:          `${props.appName}ModelsTable`,
            partitionKey:       { name: 'dataset', type: AttributeType.STRING },
        });

        this.mlTrainingInstanceStack = new InstanceStack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}MLTrainingInstanceStack`,
            id:                 `${props.appName}MLTrainingInstance`,
            instanceType:       props.mlTrainingInstanceType,
            machineImage:       props.mlTrainingMachineImage,
            keyname:            props.mlTrainingKeyPairName,
            startup:            props.mlTrainingStartup,
            policyStatements: [
                new GrantBucketReadPolicyStatement({
                    bucket: this.mlScriptsBucket.bucket
                }),
                new GrantBucketReadPolicyStatement({
                    bucket: this.mlDatasetsBucket.bucket
                }),
                new GrantBucketPutPolicyStatement({
                    bucket: this.mlModelsBucket.bucket
                }),
                new GrantTableReadWritePolicyStatement({
                    table:  this.modelsTableStack.table
                })
            ]
        });

        this.ingestionInstanceStack = new InstanceStack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}IngestionInstanceStack`,
            id:                 `${props.appName}IngestionInstance`,
            instanceType:       props.ingestionInstanceType,
            machineImage:       props.ingestionMachineImage,
            keyname:            props.ingestionKeyPairName,
            startup:            props.ingestionStartup,
            policyStatements: [
                new GrantBucketReadPolicyStatement({
                    bucket: this.mlModelsBucket.bucket
                }),
                new GrantBucketReadPolicyStatement({
                    bucket: this.datasetsBucket.bucket
                }),
                new GrantBucketReadPolicyStatement({
                    bucket: this.ingestionScriptsBucket.bucket
                }),
                new GrantTableReadWritePolicyStatement({
                    table:  this.ingestionTableStack.table
                })
            ]
        });

        this.algorithmicInstanceStack = new InstanceStack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}AlgorithmicInstanceStack`,
            id:                 `${props.appName}AlgorthmicInstance`,
            instanceType:       props.algorithmicInstanceType,
            machineImage:       props.algorithmicMachineImage,
            keyname:            props.algorithmicKeyPairName,
            startup:            props.algorithmicStartup,
            policyStatements:   [                new GrantBucketReadPolicyStatement({
                bucket: this.mlScriptsBucket.bucket
            })]
        });

        this.trainingSSMDocumentStack = new SSMDocumentStack(this, {
            account:            props.account,
            region:             props.region,
            stackId:            `${props.appName}SSMDocumentStack`,
            id:                 `${props.appName}SSMDocument`,
            name:               props.trainingSSMDocument.Name,
            type:               props.trainingSSMDocument.Type,
            targetType:         props.trainingSSMDocument.TargetType,
            version:            props.trainingSSMDocument.Version,
            updateMethod:       props.trainingSSMDocument.UpdateMethod,
            content:            props.trainingSSMDocument.Content
        });

    }

}