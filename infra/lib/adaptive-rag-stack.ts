import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import * as opensearchserverless from "aws-cdk-lib/aws-opensearchserverless";
import { RemovalPolicy } from "aws-cdk-lib";

export class AdaptiveRagStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Optional: pass --context keyPairName=my-key-pair to enable SSH with a key file.
    // If omitted, use EC2 Instance Connect (browser SSH in the AWS console) instead.
    const keyPairName = this.node.tryGetContext("keyPairName") as string | undefined;

    // -----------------------------------------------------------------------
    // DynamoDB Tables
    // -----------------------------------------------------------------------
    const jobsTable = new dynamodb.Table(this, "JobsTable", {
      tableName: "Jobs",
      partitionKey: { name: "job_id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const recordsTable = new dynamodb.Table(this, "RecordsTable", {
      tableName: "Records",
      partitionKey: { name: "record_id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    recordsTable.addGlobalSecondaryIndex({
      indexName: "job-id-index",
      partitionKey: { name: "job_id", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    const uiCacheTable = new dynamodb.Table(this, "UICacheTable", {
      tableName: "UICache",
      partitionKey: { name: "query_pattern_hash", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY,
      timeToLiveAttribute: "ttl",
    });

    const usersTable = new dynamodb.Table(this, "UsersTable", {
      tableName: "Users",
      partitionKey: { name: "user_id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    usersTable.addGlobalSecondaryIndex({
      indexName: "username-index",
      partitionKey: { name: "username", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // -----------------------------------------------------------------------
    // S3 — raw file storage
    // -----------------------------------------------------------------------
    const dataBucket = new s3.Bucket(this, "DataBucket", {
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.PUT, s3.HttpMethods.GET],
          allowedOrigins: ["*"],
          allowedHeaders: ["*"],
        },
      ],
    });

    // -----------------------------------------------------------------------
    // OpenSearch Serverless (vector search)
    // -----------------------------------------------------------------------
    const collectionName = "adaptive-rag";

    const encryptionPolicy = new opensearchserverless.CfnSecurityPolicy(this, "EncryptionPolicy", {
      name: `${collectionName}-enc`,
      type: "encryption",
      policy: JSON.stringify({
        Rules: [{ ResourceType: "collection", Resource: [`collection/${collectionName}`] }],
        AWSOwnedKey: true,
      }),
    });

    const networkPolicy = new opensearchserverless.CfnSecurityPolicy(this, "NetworkPolicy", {
      name: `${collectionName}-net`,
      type: "network",
      policy: JSON.stringify([
        {
          Rules: [
            { ResourceType: "collection", Resource: [`collection/${collectionName}`] },
            { ResourceType: "dashboard", Resource: [`collection/${collectionName}`] },
          ],
          AllowFromPublic: true,
        },
      ]),
    });

    const collection = new opensearchserverless.CfnCollection(this, "VectorCollection", {
      name: collectionName,
      type: "VECTORSEARCH",
    });
    collection.addDependency(encryptionPolicy);
    collection.addDependency(networkPolicy);

    // -----------------------------------------------------------------------
    // IAM Roles for EC2
    // AmazonSSMManagedInstanceCore lets you SSH via Session Manager in the
    // AWS console — no key pair or open port 22 required.
    // -----------------------------------------------------------------------

    // Backend role — full AWS service access (DynamoDB, S3, Bedrock, OpenSearch)
    const backendRole = new iam.Role(this, "BackendEC2Role", {
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMManagedInstanceCore"),
      ],
    });

    jobsTable.grantReadWriteData(backendRole);
    recordsTable.grantReadWriteData(backendRole);
    uiCacheTable.grantReadWriteData(backendRole);
    usersTable.grantReadWriteData(backendRole);
    dataBucket.grantReadWrite(backendRole);

    backendRole.addToPolicy(new iam.PolicyStatement({
      actions: ["bedrock:InvokeModel"],
      resources: ["*"],
    }));
    backendRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        "aws-marketplace:ViewSubscriptions",
        "aws-marketplace:Subscribe",
        "aws-marketplace:Unsubscribe",
      ],
      resources: ["*"],
    }));
    backendRole.addToPolicy(new iam.PolicyStatement({
      actions: ["aoss:APIAccessAll"],
      resources: [collection.attrArn],
    }));

    // Frontend role — SSM only (nginx serves static files, no AWS API calls)
    const frontendRole = new iam.Role(this, "FrontendEC2Role", {
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMManagedInstanceCore"),
      ],
    });

    // -----------------------------------------------------------------------
    // OpenSearch data access policy — backend role as principal
    // -----------------------------------------------------------------------
    const accessPolicy = new opensearchserverless.CfnAccessPolicy(this, "AccessPolicy", {
      name: `${collectionName}-access`,
      type: "data",
      policy: JSON.stringify([
        {
          Rules: [
            {
              ResourceType: "index",
              Resource: [`index/${collectionName}/*`],
              Permission: [
                "aoss:CreateIndex",
                "aoss:DeleteIndex",
                "aoss:UpdateIndex",
                "aoss:DescribeIndex",
                "aoss:ReadDocument",
                "aoss:WriteDocument",
              ],
            },
            {
              ResourceType: "collection",
              Resource: [`collection/${collectionName}`],
              Permission: ["aoss:CreateCollectionItems"],
            },
          ],
          Principal: [backendRole.roleArn],
        },
      ]),
    });
    accessPolicy.addDependency(collection);

    // -----------------------------------------------------------------------
    // VPC — shared by both instances
    // -----------------------------------------------------------------------
    const vpc = ec2.Vpc.fromLookup(this, "DefaultVpc", { isDefault: true });

    // Backend security group — FastAPI on port 8000
    const backendSg = new ec2.SecurityGroup(this, "BackendSG", {
      vpc,
      description: "Adaptive RAG API backend (FastAPI)",
      allowAllOutbound: true,
    });
    backendSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(8000), "FastAPI");
    // Uncomment to allow SSH via key pair instead of Session Manager:
    // backendSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), "SSH");

    // Frontend security group — nginx on port 80
    const frontendSg = new ec2.SecurityGroup(this, "FrontendSG", {
      vpc,
      description: "Adaptive RAG frontend (nginx)",
      allowAllOutbound: true,
    });
    frontendSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), "HTTP");
    // Uncomment to allow SSH via key pair instead of Session Manager:
    // frontendSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), "SSH");

    const keyPair = keyPairName
      ? ec2.KeyPair.fromKeyPairName(this, "KeyPair", keyPairName)
      : undefined;

    // -----------------------------------------------------------------------
    // Backend EC2 — FastAPI + uvicorn on port 8000, t3.small (needs headroom
    // for Bedrock calls and OpenSearch I/O)
    // -----------------------------------------------------------------------
    const backendInstance = new ec2.Instance(this, "BackendServer", {
      vpc,
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
      machineImage: ec2.MachineImage.latestAmazonLinux2023(),
      securityGroup: backendSg,
      role: backendRole,
      keyPair,
      blockDevices: [
        {
          deviceName: "/dev/xvda",
          volume: ec2.BlockDeviceVolume.ebs(20),
        },
      ],
    });

    // -----------------------------------------------------------------------
    // Frontend EC2 — nginx serving static React files on port 80, t2.micro
    // (no compute work — free tier eligible)
    // -----------------------------------------------------------------------
    const frontendInstance = new ec2.Instance(this, "FrontendServer", {
      vpc,
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
      machineImage: ec2.MachineImage.latestAmazonLinux2023(),
      securityGroup: frontendSg,
      role: frontendRole,
      keyPair,
    });

    // Basic CloudWatch log group for app logs
    new logs.LogGroup(this, "AppLogs", {
      logGroupName: "/adaptive-rag/app",
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // -----------------------------------------------------------------------
    // Outputs
    // -----------------------------------------------------------------------
    new cdk.CfnOutput(this, "BackendInstanceId", {
      value: backendInstance.instanceId,
      description: "Backend EC2 instance ID — use for Session Manager SSH",
    });
    new cdk.CfnOutput(this, "FrontendInstanceId", {
      value: frontendInstance.instanceId,
      description: "Frontend EC2 instance ID — use for Session Manager SSH",
    });
    new cdk.CfnOutput(this, "ApiUrl", {
      value: `http://${backendInstance.instancePublicIp}:8000`,
      description: "FastAPI backend — paste into VITE_API_URL when building frontend",
    });
    new cdk.CfnOutput(this, "FrontendUrl", {
      value: `http://${frontendInstance.instancePublicIp}`,
      description: "React frontend served by nginx on port 80",
    });
    new cdk.CfnOutput(this, "DataBucketName", {
      value: dataBucket.bucketName,
      description: "Paste into S3_BUCKET in .env on the backend instance",
    });
    new cdk.CfnOutput(this, "OpenSearchEndpoint", {
      value: collection.attrCollectionEndpoint,
      description: "Paste into OPENSEARCH_ENDPOINT in .env on the backend instance",
    });
  }
}
