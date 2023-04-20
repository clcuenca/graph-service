/**
 * Pipeline stack
 * @author Carlos L. Cuenca
 * @version 1.0.0
 */

import { Construct } from 'constructs'
import { Stage, Stack } from 'aws-cdk-lib'
import {CodePipeline, CodePipelineSource, FileSet, FileSetLocation, ShellStep} from 'aws-cdk-lib/pipelines'
import {CodeCommitTrigger, CodeDeployServerDeployAction} from 'aws-cdk-lib/aws-codepipeline-actions'
import { Repository } from 'aws-cdk-lib/aws-codecommit'
import {
    InstanceTagSet,
    ServerApplication,
    ServerDeploymentConfig,
    ServerDeploymentGroup
} from "aws-cdk-lib/aws-codedeploy";

/// ----------
/// Properties

export interface PipelineStackProps {
    account:            string,
    region:             string,
    stackId:            string,
    pipelineId:         string,
    repository:         string,
    branch:             string,
    outputDirectory:    string,
    commands:           string[],
    trigger:            CodeCommitTrigger,
    selfMutation:       boolean,
    stages:             Stage[],
}

export interface Application {
    fileSet:    FileSet,
    directory:  string,
}

/// --------------------
/// Class Implementation

export class PipelineStack extends Stack {

    /// ---------------
    /// Private Members

    private readonly repository:                Repository                      ;
    private readonly pipeline:                  CodePipeline                    ;

    /// -----------
    /// Constructor

    constructor(scope: Construct, props: PipelineStackProps) {
        super(scope, props.stackId, { env: {
                account: props.account,
                region:  props.region
            }});

        this.repository = new Repository(this, `${props.repository}Id`, {
            repositoryName: props.repository
        });

        this.pipeline = new CodePipeline(this, props.pipelineId, {
            selfMutation:   props.selfMutation,
            synth:          new ShellStep(`${props.pipelineId}ShellStep`, {
                input:  CodePipelineSource.codeCommit(this.repository, props.branch, {
                    trigger: props.trigger
                }),
                commands:               props.commands,
                primaryOutputDirectory: props.outputDirectory
            }),
        });

        props.stages.forEach((stage) => {
            this.pipeline.addStage(stage);
        });

    }

}
