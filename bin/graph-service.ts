#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { GraphServiceStack } from '../lib/graph-service-stack';
import {PipelineStack} from "../lib/pipeline-stack";
import {Constants} from "../lib/constants";
import {AlphaStage} from "../lib/alpha-stage";
import {App} from "aws-cdk-lib";
import {IMachineImage, InstanceType} from "aws-cdk-lib/aws-ec2";

const app = new App();

const alphaStage = new AlphaStage(app, {
    account:                Constants.Account,
    region:                 Constants.Region,
    stageId:                Constants.Stages.Alpha.Id,
    stageName:              Constants.Stages.Alpha.Name,
    appName:                Constants.AppName,
    ec2ServicePrincipal:    Constants.EC2.ServicePrincipal,
    mlTrainingInstanceType: Constants.EC2.Instance.MLTraining.Type,
    mlTrainingMachineImage: Constants.EC2.Instance.MLTraining.Image,
    mlTrainingKeyPairName:  Constants.EC2.Instance.MLTraining.KeyPairName,
    mlTrainingStartup:      Constants.EC2.Instance.MLTraining.Startup,
    ingestionInstanceType:  Constants.EC2.Instance.Ingestion.Type,
    ingestionMachineImage:  Constants.EC2.Instance.Ingestion.Image,
    ingestionKeyPairName:   Constants.EC2.Instance.Ingestion.KeyPairName,
    ingestionStartup:       Constants.EC2.Instance.Ingestion.Startup,
    trainingSSMDocument:    Constants.EC2.Instance.MLTraining.Document
});

const pipelineStack = new PipelineStack(app, {
    account:            Constants.Account,
    region:             Constants.Region,
    stackId:            `${Constants.AppName}PipelineStack`,
    pipelineId:         `${Constants.AppName}Pipeline`,
    repository:         Constants.CodeCommit.Repository.Name,
    branch:             Constants.CodeCommit.Branches.Main,
    outputDirectory:    Constants.CodeCommit.Repository.OutputDirectory,
    commands:           Constants.CodeCommit.Repository.Commands,
    trigger:            Constants.CodeCommit.Trigger,
    selfMutation:       Constants.CodePipeline.SelfMutate,
    stages:             [alphaStage]
});

app.synth();
