/// <reference path="./.sst/platform/config.d.ts" />

export default $config({
  app(input) {
    return {
      name: "ainewsbot",
      removal: input?.stage === "production" ? "retain" : "remove",
      home: "aws",
      providers: {
        aws: {
          region: "us-east-1",
        },
      },
    };
  },
  async run() {
    // Configure SES Email
    const email = new sst.aws.Email("AInewsbotEmail", {
      sender: $app.stage === "production" 
        ? process.env.SES_PROD_SENDER || "ainews@yourdomain.com"  // Production domain
        : process.env.SES_DEV_SENDER || "ainews-dev@yourdomain.com",  // Dev email
    });

    // Optional: Test function to verify SES is working
    const testFunction = new sst.aws.Function("EmailTest", {
      handler: "ainewsbot/ses_test.handler",
      link: [email],
      environment: {
        STAGE: $app.stage,
        SES_SENDER_EMAIL: email.sender,
      },
      runtime: "python3.11",
    });

    // Output the configuration
    return {
      emailSender: email.sender,
      testFunctionArn: testFunction.arn,
      stage: $app.stage,
    };
  },
});