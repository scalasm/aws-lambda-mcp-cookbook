---
title: Homepage
description: AWS Lambda MCP Cookbook - a Serverless MCP Server Blueprint
---
## **AWS AWS Lambda MCP Cookbook - a Serverless MCP Server Blueprint**

[<img alt="alt_text" src="./media/banner.png" width="400" />](https://www.ranthebuilder.cloud/)

## **The Problem**

Starting a production grade Serverless MCP can be overwhelming. You need to figure out many questions and challenges that have nothing to do with your business domain:

* How to deploy to the cloud? What IAC framework do you choose?
* How to write a SaaS-oriented CI/CD pipeline? What does it need to contain?
* How do you handle observability, logging, tracing, metrics?
* How do you write a production grade Lambda function?
* How do you handle testing?
* What makes an AWS Lambda handler resilient, traceable, and easy to maintain? How do you write such a code?

## **The Solution**

This project aims to reduce cognitive load and answer these questions for you by providing a skeleton Python Serverless service blueprint that implements best practices for AWS Lambda, Serverless CI/CD, and AWS CDK in one blueprint project.

This project is a blueprint for new Serverless MCP servers.

It provides two implementation options:

1. Pure, native Lambda function with no FastMCP.
2. Lambda with AWS web adapter and FastMCP

Choose the architecture that you see fit, each with its own pros and cons.

![design](https://github.com/ran-isenberg/aws-lambda-mcp-cookbook/blob/main/docs/media/design.png?raw=true)

### Option 1: Serverless Native Lambda MCP Server

This project provides a working, open source based, AWS Lambda based Python MCP server implementation.

The MCP server uses JSON RPC over HTTP (non streamable) via API Gateway's body payload parameter. See integration tests and see how the test event is generated.

It contains an advanced implementation including IaC CDK code and a CI/CD pipeline, testing, observability and more (see Features section).

It's started based on [AWS sample for MCP](https://github.com/awslabs/mcp/tree/main/src/mcp-lambda-handler) - but had major refactors since, combined with the [AWS Lambda Handler cookbook](https://ran-isenberg.github.io/aws-lambda-handler-cookbook/) template.

Better fitted for POCs or tool oriented MCPs. Can be secured with custom authentication code and WAF.

### Option 2: Serverless Lambda Web Adapter & FastMCP

Based on [AWS Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter) and [FastMCP](https://github.com/jlowin/fastmcp).

Use an HTTP API GW and Lambda function. Can be used with a REST API GW with a custom domain too.

Better fitted for production-grade MCP servers as it upholds to the official MCP protocol and has native auth mechanism (OAuth).

#### **Monitoring Design**

<img alt="monitoring" src="./media/monitoring_design.png" />

### **Features**

* PURE Lambda - not web adapter, no FastMCP required or Web adapter with FastMCP.
* Python Serverless MCP server with a recommended file structure.
* MCP Tools input validation: check argument types and values
* CDK infrastructure with infrastructure tests and security tests.
* Tests - unit, integration (tests for full MCP messages) and E2E with a real MCP client
* CI/CD pipelines based on Github actions that deploys to AWS with python linters, complexity checks and style formatters.
* CI/CD pipeline deploys to dev/staging and production environments with different gates between each environment
* Makefile for simple developer experience.
* The AWS Lambda handler embodies Serverless best practices and has all the bells and whistles for a proper production ready handler.
* AWS Lambda handler uses [AWS Lambda Powertools](https://docs.powertools.aws.dev/lambda-python/).
* AWS Lambda handler 3 layer architecture: handler layer, logic layer and data access layer
* Session context storage in DynamoDB - global getter and setter (get_session, set_session) - be advised, has security issue - need to match session id to user
* API protected by WAF with four AWS managed rules in production deployment
* CloudWatch dashboards - High level and low level including CloudWatch alarms

The GitHub blueprint project can be found at [https://github.com/ran-isenberg/aws-lambda-mcp-cookbook](https://github.com/ran-isenberg/aws-lambda-mcp-cookbook){:target="_blank" rel="noopener"}.

## **Serverless Best Practices**

The AWS Lambda handler will implement multiple best practice utilities.

Each utility is implemented when a new blog post is published about that utility.

The utilities cover multiple aspects of a production-ready service, including:

* [**Logging**](best_practices/logger.md)
* [**Observability: Monitoring and Tracing**](best_practices/tracer.md)
* [**Observability: Business KPI Metrics**](best_practices/metrics.md)
* [**Environment Variables**](best_practices/environment_variables.md)
* [**Hexagonal Architecture**](https://www.ranthebuilder.cloud/post/learn-how-to-write-aws-lambda-functions-with-architecture-layers)
* [**Input Validation**](best_practices/input_validation.md)
* [**Serverless Monitoring**](https://www.ranthebuilder.cloud/post/how-to-effortlessly-monitor-serverless-applications-with-cloudwatch-part-one)
* [**Learn How to Write AWS Lambda Functions with Three Architecture Layers**](https://www.ranthebuilder.cloud/post/learn-how-to-write-aws-lambda-functions-with-architecture-layers){:target="_blank" rel="noopener"}

While the code examples are written in Python, the principles are valid to any supported AWS Lambda handler programming language.

## Security

For pure Lambda:

* WAF connected in production accounts (requires having an environment variable during deployment called 'ENVIRONMENT' with a value of 'production')
* Auth/Authz function placeholder in the mcp.py handler function - see authentication.py
* It is recommended to either use IAM/Cognito/Lambda authorizer or use the authentication.py and implement identity provider token validation flow.

For FastMCP:

* Use FastMCP Auth parameter for Oauth implementation.
* If you use session id management, you need to make sure the session id matches the user id by yourself.

### Known Issues

* There might be security issues with this implementation, MCP is very new and has many issues.
* Session saving - there's no match validation between session id and user id/tenant id. This is a TODO item.
* It is not possible to manually update session data, only fetch.
* Pure Lambda variation has limited MCP protocol support, it's based used for tools only simple MCP. For full blown services, use the FastMCP variation.

## Handler Examples

Pure Lambda:

```python hl_lines="8 13 38" title="service/handlers/mcp.py"
--8<-- "docs/examples/best_practices/mcp/mcp.py"
```

Handler is found at service/handlers/mcp.py

MCP engine found at service/mcp_lambda_handler folder

FastMCP Lambda:

```python hl_lines="8 11 19 26 33" title="service/mcp_server.py"
--8<-- "docs/examples/best_practices/mcp/mcp_server.py"
```

Handler is found at service/mcp_server.py

## **License**

This library is licensed under the MIT License. See the [LICENSE](https://github.com/ran-isenberg/aws-lambda-mcp-cookbook/blob/main/LICENSE) file.
