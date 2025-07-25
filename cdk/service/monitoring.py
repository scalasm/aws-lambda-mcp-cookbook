from typing import Union

import aws_cdk.aws_sns as sns
from aws_cdk import Duration, RemovalPolicy, aws_apigateway
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as _lambda
from cdk_monitoring_constructs import (
    AlarmFactoryDefaults,
    CustomMetricGroup,
    ErrorRateThreshold,
    LatencyThreshold,
    MetricStatistic,
    MonitoringFacade,
    SnsAlarmActionStrategy,
)
from constructs import Construct

from cdk.service import constants


class Monitoring(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        mcp_api: Union[aws_apigateway.RestApi, apigwv2.HttpApi],
        db: dynamodb.TableV2,
        functions: list[_lambda.Function],
    ) -> None:
        super().__init__(scope, id_)
        self.id_ = id_
        self.notification_topic = self._build_topic()
        self._build_high_level_dashboard(mcp_api, self.notification_topic)
        self._build_low_level_dashboard(db, functions, self.notification_topic)

    def _build_topic(self) -> sns.Topic:
        key = kms.Key(
            self,
            'MonitoringKey',
            description='KMS Key for SNS Topic Encryption',
            enable_key_rotation=True,  # Enables automatic key rotation
            removal_policy=RemovalPolicy.DESTROY,
            pending_window=Duration.days(7),
        )
        topic = sns.Topic(self, f'{self.id_}alarms', display_name=f'{self.id_}alarms', master_key=key)
        # Grant CloudWatch permissions to publish to the SNS topic
        topic.add_to_resource_policy(
            statement=iam.PolicyStatement(
                actions=['sns:Publish'],
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal('cloudwatch.amazonaws.com')],
                resources=[topic.topic_arn],
            )
        )
        return topic

    def _build_high_level_dashboard(
        self,
        mcp_api: Union[aws_apigateway.RestApi, apigwv2.HttpApi],
        topic: sns.Topic,
    ):
        high_level_facade = MonitoringFacade(
            self,
            f'{self.id_}HighFacade',
            alarm_factory_defaults=AlarmFactoryDefaults(
                actions_enabled=True,
                alarm_name_prefix=self.id_,
                action=SnsAlarmActionStrategy(on_alarm_topic=topic),
            ),
        )
        high_level_facade.add_large_header('MCP Server High Level Dashboard')
        high_level_facade.monitor_api_gateway(
            api=mcp_api,  # type: ignore
            add5_xx_fault_rate_alarm={'internal_error': ErrorRateThreshold(max_error_rate=1)},
        )
        metric_factory = high_level_facade.create_metric_factory()
        create_metric = metric_factory.create_metric(
            metric_name='ValidMcpEvents',
            namespace=constants.METRICS_NAMESPACE,
            statistic=MetricStatistic.N,
            dimensions_map={constants.METRICS_DIMENSION_KEY: constants.SERVICE_NAME},
            label='MCP events',
            period=Duration.days(1),
        )

        group = CustomMetricGroup(metrics=[create_metric], title='Daily MCP Requests')
        high_level_facade.monitor_custom(metric_groups=[group], human_readable_name='Daily KPIs', alarm_friendly_name='KPIs')

    def _build_low_level_dashboard(self, db: dynamodb.TableV2, functions: list[_lambda.Function], topic: sns.Topic):
        low_level_facade = MonitoringFacade(
            self,
            f'{self.id_}LowFacade',
            alarm_factory_defaults=AlarmFactoryDefaults(
                actions_enabled=True,
                alarm_name_prefix=self.id_,
                action=SnsAlarmActionStrategy(on_alarm_topic=topic),
            ),
        )
        low_level_facade.add_large_header('MCP Server Low Level Dashboard')
        for func in functions:
            low_level_facade.monitor_lambda_function(
                lambda_function=func,
                add_latency_p90_alarm={'p90': LatencyThreshold(max_latency=Duration.seconds(3))},
            )
            low_level_facade.monitor_log(
                log_group_name=func.log_group.log_group_name,
                human_readable_name='Error logs',
                pattern='ERROR',
                alarm_friendly_name='error logs',
            )

        low_level_facade.monitor_dynamo_table(table=db, billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST)
