/**
 * Constants File
 * @author Kirsten Tan
 * @author Carlos L. Cuenca
 * @version 0.1.0
 */

import { CodeCommitTrigger } from 'aws-cdk-lib/aws-codepipeline-actions'
import { Runtime } from 'aws-cdk-lib/aws-lambda'
import {AmazonLinuxGeneration, AmazonLinuxImage, InstanceClass, InstanceSize, InstanceType} from "aws-cdk-lib/aws-ec2";
import {App} from "aws-cdk-lib";

export module Constants {

    /// ---
    /// App

    /**
     * The user account id that owns the app.
     */
    export const Account        = '669680791620'    ;
    /**
     * The region where all the app's resources will be deployed.
     */
    export const Region         = 'us-east-1'       ;
    /**
     * The name of the app; corresponds with the CodeCommit repository
     */
    export const AppName        = 'graph-service'   ;
    /**
     * The domain corresponding with the app's front-end
     */
    export const Domain         = ''                ;

    /// ------
    /// Stages

    /**
     * The App's deployment stages
     */
    export module Stages {

        /// -----
        /// Alpha

        export module Alpha {

            export const Name   = 'Alpha'           ;
            export const Id     = `${Name}Stage`    ;

        }

    }

    /// -----------
    /// Code Commit

    /**
     * Values & fields that correspond with CodeCommit integration.
     */
    export module CodeCommit {

        /**
         * Where the application code is output
         */
        export const PrimaryOutputDirectory = 'cdk.out'                             ;
        /**
         * The CodeCommit action that triggers the pipeline
         */
        export const Trigger                = CodeCommitTrigger.POLL                ;

        /// ----------
        /// Repository

        /**
         * Values that correspond to the CodeCommit
         */
        export module Repository {

            export const Name               = 'graph-service'                       ;
            export const OutputDirectory    = 'cdk.out'                             ;
            export const Commands           = [
                'npm install typescript',
                'npm install aws-cdk-lib',
                'npm i constructs @aws-cdk/assets @aws-cdk/region-info',
                'npm uninstall -g aws-cdk',
                'npm install -g aws-cdk',
                'npx cdk synth'
            ]
        }

        /// --------
        /// Branches

        export module Branches {

            export const Main = 'master'                                            ;

        }

    }

    /// -------------
    /// Code Pipeline

    export module CodePipeline {

        export const SelfMutate =   true                                            ;

    }

    /// --
    /// S3

    export module S3 {

        /// -------
        /// Buckets

        export module Bucket {

            /// ---------------
            /// Datasets Bucket

            export module Datasets {

                export const Name   = `${AppName}-datasets-bucket`  ;
                export const Id     = `${AppName}DatasetsBucket`    ;

            }

            /// ------------------------
            /// Ingestion Scripts Bucket

            export module IngestionScripts {

                export const Name   = `${AppName}-ingestion-scripts-bucket` ;
                export const Id     = `${AppName}IngestionScriptsBucket`    ;

            }

            /// ------------------
            /// ML Datasets Bucket

            export module MLDatasets {

                export const Name   = `${AppName}-ml-datasets-bucket`   ;
                export const Id     = `${AppName}MLDatasetsBucket`      ;

            }

            /// ------------------
            /// ML Datasets Bucket

            export module MLModels {

                export const Name   = `${AppName}-ml-models-bucket`   ;
                export const Id     = `${AppName}MLModelsBucket`      ;

            }

            /// -----------------
            /// ML Scripts Bucket

            export module MLScripts {

                export const Name   = `${AppName}-ml-scripts-bucket`   ;
                export const Id     = `${AppName}MLScriptsBucket`      ;

            }

        }

    }

    /// ---
    /// EC2

    export module EC2 {

        export const ServicePrincipal = 'ec2.amazonaws.com';

        /// --------
        /// Instance

        export module Instance {

            /// -----------
            /// ML Training

            export module MLTraining {

                export const Type = InstanceType.of(InstanceClass.BURSTABLE2, InstanceSize.MICRO)

                export const Image = new AmazonLinuxImage({
                    generation: AmazonLinuxGeneration.AMAZON_LINUX_2,
                });

                export const KeyPairName = 'graph-service-ml-training-key';

                export const Startup = []

                /// ------------
                /// SSM Document

                export module Document {

                    export const Type           = 'Command'             ;
                    export const TargetType     = '/AWS::EC2::Instance' ;
                    export const Name           = 'TrainingRunDocument5';
                    export const UpdateMethod   = 'Replace'             ;
                    export const Scripts        = 'mlscripts.zip'       ;
                    export const Content = {
                        schemaVersion: '2.2',
                        parameters: {
                            script: {
                                type: 'String',
                                default: 'textcat_train.py'
                            },
                            dataset: {
                                type: 'String',
                                default: 'hatecheck.csv'
                            },
                            model: {
                                type: 'String',
                                default: 'en_core_web_lg',
                                allowedValues: [
                                    'en_core_web_sm',
                                    'en_core_web_md',
                                    'en_core_web_lg',
                                    'en_core_web_trf'
                                ]
                            },
                            parameters: {
                                type: 'String',
                                default: '--pipe_name textcat --labels POSITIVE NEGATIVE --omit NEGATIVE'
                            }
                        },
                        mainSteps: [
                            {
                                action: 'aws:runShellScript',
                                name:   'RetrieveScripts',
                                inputs: {
                                    runCommand: [
                                        `rm -f *.py && rm -f .*.py`,
                                        `aws s3api get-object --bucket ${S3.Bucket.MLScripts.Name} `+
                                        `--key ${Scripts} ${Scripts}`,
                                        `unzip -j ${Scripts}`,
                                        `rm ${Scripts}`,
                                        `python3 {{ script }} `+
                                        `--datasetbucket ${S3.Bucket.MLDatasets.Name} `+
                                        `--modelsbucket ${S3.Bucket.MLModels.Name} `+
                                        `--dataset {{ dataset }} `+
                                        `--model {{ model }} ` +
                                        `{{ parameters }}`
                                    ]
                                }
                            }
                        ]
                    }
                }
            }

            /// ---------
            /// Ingestion

            export module Ingestion {

                export const Type = InstanceType.of(InstanceClass.BURSTABLE2, InstanceSize.MICRO)

                export const Image = new AmazonLinuxImage({
                    generation: AmazonLinuxGeneration.AMAZON_LINUX_2,
                });

                export const KeyPairName = 'graph-service-ingestion-key';

                export const Startup = []

                export module Document {

                    export const Type           = 'Command'                 ;
                    export const TargetType     = '/AWS::EC2::Instance'     ;
                    export const Name           = 'IngestionRunDocument5'   ;
                    export const UpdateMethod   = 'Replace'                 ;
                    export const Scripts        = 'ingestionscripts.zip'    ;
                    export const Content = {
                        schemaVersion: '2.2',
                        parameters: {
                            script: {
                                type: 'String'
                            },
                            dataset: {
                                type: 'String'
                            },
                            model_name: {
                                type: 'String'
                            },
                            model: {
                                type: 'String',
                                default: 'en_core_web_lg',
                                allowedValues: [
                                    'en_core_web_sm',
                                    'en_core_web_md',
                                    'en_core_web_lg',
                                    'en_core_web_trf'
                                ]
                            },
                            endpoint: {
                                type: 'String'
                            },
                            region: {
                                type: 'String',
                                default: Region
                            }
                        },
                        mainSteps: [
                            {
                                action: 'aws:runShellScript',
                                name:   'RetrieveScripts',
                                inputs: {
                                    runCommand: [
                                        `rm -f *.py && rm -f .*.py`,
                                        `aws s3api get-object --bucket ${S3.Bucket.IngestionScripts.Name} --key ${Scripts} ${Scripts}`,
                                        `unzip -j ${Scripts}`,
                                        `rm ${Scripts}`,
                                        `python3 {{ script }} ` +
                                        `--datasetsbucket ${S3.Bucket.Datasets.Name}` +
                                        `--dataset {{ dataset }} `+
                                        `--dataset_model {{ dataset_model }} ` +
                                        `--modelsbucket ${S3.Bucket.MLModels.Name} ` +
                                        `--model {{ model }} ` +
                                        `--endpoint {{ endpoint }} ` +
                                        `--region {{ region }}`
                                    ]

                                }

                            }

                        ]

                    }

                }

            }

        }

    }

    /// ------
    /// Lambda

    export module Lambda {

        export const Principal  =   'lambda.amazonaws.com'  ;

        export module APILambda {

            export const Handler    = 'index.handler'       ;
            export const Run        = Runtime.PYTHON_3_9    ;
            export const CodePath   = 'lib/lambda.zip'      ;
            export const Retry      = 2                     ;
            export const Timeout    = 15                    ;

        }

    }

}