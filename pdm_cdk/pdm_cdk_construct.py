from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as targets,
)
import aws_cdk as core
from constructs import Construct
from typing import Dict

class PdmCdkConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        config: Dict[str, str],
        environment: str,
        tags: Dict[str, str],
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        vpc = self.get_vpc(config, app_name, environment)

        ec2_instace = self.create_ec2(config, app_name, vpc)

    def get_vpc(self, config, app_name, environment):
        """
        Either create a new VPC with options or import an existing one
        """

        if config.get("create_new_vpc") is True:
            vpc = ec2.Vpc(
                self,
                f"{app_name}-vpc",
                vpc_name=f"{app_name}-{environment}-vpc",
                max_azs=config.get("vpc").get("max_azs"),
                cidr=config.get("vpc").get("cide_range"),
                nat_gateways=config.get("vpc").get("nat_gateways"),
                subnet_configuration=[
                    ec2.SubnetConfiguration(
                        name="public", subnet_type=ec2.SubnetType.PUBLIC
                    ),
                    ec2.SubnetConfiguration(
                        name="private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                    ),
                ],
            )

            core.CfnOutput(
                self, "VpcId", value=vpc.vpc_id, export_name="xray-app-vpcid"
            )

        else:
            vpc = ec2.Vpc.from_lookup(
                self, f"{app_name}-vpc", vpc_name=config.get("vpc").get("existing_vpc")
            )

        return vpc


    def create_ec2(self, config, app_name, vpc):
        """
        Create an EC2 instance with custom config
        """

        ami_id = config.get("ec2").get("ami")
        instance_size = config.get("ec2").get("instance_type")
        ebs_size = config.get("ec2").get("ebs")

        alb_sg = ec2.SecurityGroup(self, "ALBSecurityGroup", 
                           vpc=vpc, 
                           description="Security group for ALB")

        # Add inbound rules to the security group for HTTP and HTTPS
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))

        # Create the ALB
        alb = elbv2.ApplicationLoadBalancer(self, "ALB",
                                            vpc=vpc,
                                            internet_facing=True,
                                            security_group=alb_sg)

        # Create Security Group
        sg = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
            description="Allow ssh and web access to ec2 instances",
            allow_all_outbound=True 
        )
        sg.add_ingress_rule(alb_sg, ec2.Port.tcp(80))

        # Create IAM Role with CloudWatch access
        role = iam.Role(
            self, "Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )

        # Read Userdata file
        with open("./userdata/userdata.sh") as f:
            user_data_content = f.read()

        # Create an Amazon EC2 instance within the private subnet of the VPC
        instance = ec2.Instance(
            self,
            "Instance",
            instance_type=ec2.InstanceType(instance_type_identifier=instance_size),
            vpc=vpc,
            security_group=sg,
            role=role,
            machine_image=ec2.MachineImage.latest_amazon_linux(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            user_data=ec2.UserData.custom(user_data_content),
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            block_devices=[ec2.BlockDevice(
                device_name="/dev/xvda",
                volume=ec2.BlockDeviceVolume.ebs(ebs_size) 
            )]
        )

        # Create a listener for the ALB
        listener = alb.add_listener("Listener", 
                                    port=80,
                                    open=True)

        # Create a target group
        listener.add_targets("EC2Target",
            targets=[targets.InstanceTarget(instance)],
            port=80,
        )