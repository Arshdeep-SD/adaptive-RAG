#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { AdaptiveRagStack } from "../lib/adaptive-rag-stack";

const app = new cdk.App();
new AdaptiveRagStack(app, "AdaptiveRagStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-west-2",
  },
});
