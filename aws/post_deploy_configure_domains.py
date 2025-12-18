#!/usr/bin/env python3
"""
Post-deploy configuration for domains and certificates.

Automates the previously-manual steps:
  A) CloudFront: attach ACM cert + add aliases (repwarrior.net / www / content)
  B) API Gateway: create/ensure custom domain (api.<domain>), base path mapping, and Route53 alias record

Designed to be idempotent and safe to re-run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError


@dataclass(frozen=True)
class Config:
    region: str
    domain_name: str
    hosted_zone_id: str
    storage_stack: str
    dns_stack: str
    api_stack: str
    stage_name: str
    enable_cloudfront: bool
    enable_api_domain: bool
    wait: bool


def _log(msg: str) -> None:
    print(msg, flush=True)


def _die(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def get_stack_output(cf, stack_name: str, output_key: str) -> Optional[str]:
    try:
        resp = cf.describe_stacks(StackName=stack_name)
        outputs = resp["Stacks"][0].get("Outputs", [])
        for o in outputs:
            if o.get("OutputKey") == output_key:
                return o.get("OutputValue")
        return None
    except ClientError as e:
        _die(f"Failed to describe stack '{stack_name}': {e}")
        return None


def list_stack_resources(cf, stack_name: str) -> List[Dict[str, Any]]:
    resources: List[Dict[str, Any]] = []
    token: Optional[str] = None
    while True:
        kwargs: Dict[str, Any] = {"StackName": stack_name}
        if token:
            kwargs["NextToken"] = token
        resp = cf.list_stack_resources(**kwargs)
        resources.extend(resp.get("StackResourceSummaries", []))
        token = resp.get("NextToken")
        if not token:
            break
    return resources


def get_cloudfront_distribution_ids(cf, storage_stack: str) -> Tuple[str, str]:
    resources = list_stack_resources(cf, storage_stack)
    dist_ids = [r["PhysicalResourceId"] for r in resources if r["ResourceType"] == "AWS::CloudFront::Distribution"]
    if len(dist_ids) < 2:
        _die(
            f"Expected 2 CloudFront distributions in stack '{storage_stack}', found {len(dist_ids)}: {dist_ids}"
        )
    # Heuristic: pick by logical id prefix
    frontend = next((r["PhysicalResourceId"] for r in resources
                     if r["ResourceType"] == "AWS::CloudFront::Distribution"
                     and "FrontendDistribution" in r["LogicalResourceId"]), None)
    content = next((r["PhysicalResourceId"] for r in resources
                    if r["ResourceType"] == "AWS::CloudFront::Distribution"
                    and "ContentDistribution" in r["LogicalResourceId"]), None)
    if not frontend or not content:
        # fallback: stable ordering
        frontend, content = dist_ids[0], dist_ids[1]
    return frontend, content


def update_distribution_aliases_and_cert(
    cf_client,
    dist_id: str,
    aliases: List[str],
    cert_arn: str,
    min_tls: str = "TLSv1.2_2021",
) -> None:
    resp = cf_client.get_distribution_config(Id=dist_id)
    etag = resp["ETag"]
    cfg = resp["DistributionConfig"]

    desired_aliases = sorted(aliases)
    current_aliases = sorted((cfg.get("Aliases") or {}).get("Items") or [])

    # ViewerCertificate can be CloudFrontDefaultCertificate or ACM
    vc = cfg.get("ViewerCertificate") or {}
    current_acm = vc.get("ACMCertificateArn")

    changed = False
    if current_aliases != desired_aliases:
        cfg["Aliases"] = {"Quantity": len(aliases), "Items": aliases}
        changed = True

    # Always set to ACM + SNI
    desired_vc = {
        "ACMCertificateArn": cert_arn,
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": min_tls,
        "Certificate": cert_arn,
        "CertificateSource": "acm",
    }
    if current_acm != cert_arn or vc.get("SSLSupportMethod") != "sni-only" or vc.get("MinimumProtocolVersion") != min_tls:
        cfg["ViewerCertificate"] = desired_vc
        changed = True

    if not changed:
        _log(f"✅ CloudFront {dist_id}: already configured (aliases + cert)")
        return

    _log(f"🛠️  Updating CloudFront {dist_id}: aliases={aliases}, cert={cert_arn}")
    cf_client.update_distribution(Id=dist_id, IfMatch=etag, DistributionConfig=cfg)
    _log(f"✅ CloudFront {dist_id}: update submitted (Status will be InProgress)")


def wait_for_cloudfront_deployed(cf_client, dist_id: str, timeout_s: int = 1800) -> None:
    start = time.time()
    while True:
        status = cf_client.get_distribution(Id=dist_id)["Distribution"]["Status"]
        if status == "Deployed":
            _log(f"✅ CloudFront {dist_id}: Deployed")
            return
        if time.time() - start > timeout_s:
            _die(f"Timed out waiting for CloudFront {dist_id} to deploy (last status={status})")
        _log(f"⏳ CloudFront {dist_id}: {status} (waiting...)")
        time.sleep(20)


def get_rest_api_id(cf, api_stack: str) -> str:
    resources = list_stack_resources(cf, api_stack)
    rest_api = next((r["PhysicalResourceId"] for r in resources if r["ResourceType"] == "AWS::ApiGateway::RestApi"), None)
    if not rest_api:
        _die(f"Could not find AWS::ApiGateway::RestApi in stack '{api_stack}'")
    return rest_api


def ensure_apigw_custom_domain_and_mapping(
    apigw,
    domain_name: str,
    cert_arn: str,
    rest_api_id: str,
    stage_name: str,
) -> Tuple[str, str]:
    """
    Returns (regionalDomainName, regionalHostedZoneId)
    """
    try:
        resp = apigw.get_domain_name(domainName=domain_name)
        _log(f"✅ API Gateway domain exists: {domain_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NotFoundException":
            raise
        _log(f"🛠️  Creating API Gateway domain: {domain_name}")
        resp = apigw.create_domain_name(
            domainName=domain_name,
            endpointConfiguration={"types": ["REGIONAL"]},
            regionalCertificateArn=cert_arn,
            securityPolicy="TLS_1_2",
        )
        _log(f"✅ API Gateway domain created: {domain_name}")

    # Ensure TLS policy is TLS 1.2 (we explicitly avoid TLS 1.3 due to compatibility issues)
    current_policy = resp.get("securityPolicy")
    current_cert = resp.get("regionalCertificateArn")
    if current_policy != "TLS_1_2" or (current_cert and current_cert != cert_arn):
        patch_ops = []
        if current_policy != "TLS_1_2":
            patch_ops.append({"op": "replace", "path": "/securityPolicy", "value": "TLS_1_2"})
        # Keep certificate consistent
        if current_cert and current_cert != cert_arn:
            patch_ops.append({"op": "replace", "path": "/regionalCertificateArn", "value": cert_arn})
        if patch_ops:
            _log(f"🛠️  Updating API Gateway domain settings (TLS_1_2/cert): {domain_name}")
            apigw.update_domain_name(domainName=domain_name, patchOperations=patch_ops)
            _log("✅ API Gateway domain updated")
            resp = apigw.get_domain_name(domainName=domain_name)

    # Ensure base path mapping exists (root mapping -> stage)
    mappings = apigw.get_base_path_mappings(domainName=domain_name).get("items", [])
    has_root = any(m.get("basePath") in (None, "", "(none)") for m in mappings)
    if not has_root:
        _log(f"🛠️  Creating base path mapping: {domain_name} -> {rest_api_id} ({stage_name})")
        apigw.create_base_path_mapping(
            domainName=domain_name,
            restApiId=rest_api_id,
            stage=stage_name,
            basePath="(none)",
        )
        _log("✅ Base path mapping created")
    else:
        _log("✅ Base path mapping already exists")

    # Refresh to get regionalDomainName / hostedZoneId
    resp = apigw.get_domain_name(domainName=domain_name)
    regional_domain = resp.get("regionalDomainName")
    regional_zone = resp.get("regionalHostedZoneId")
    if not regional_domain or not regional_zone:
        _die(f"API Gateway domain '{domain_name}' did not return regionalDomainName/hostedZoneId")
    return regional_domain, regional_zone


def upsert_route53_alias_a_record(
    r53,
    hosted_zone_id: str,
    record_name: str,
    target_dns_name: str,
    target_hosted_zone_id: str,
) -> None:
    # Ensure trailing dot for alias target per AWS API expectations
    dns = target_dns_name if target_dns_name.endswith(".") else f"{target_dns_name}."
    name = record_name if record_name.endswith(".") else f"{record_name}."

    change_batch = {
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": name,
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId": target_hosted_zone_id,
                        "DNSName": dns,
                        "EvaluateTargetHealth": False,
                    },
                },
            }
        ]
    }
    _log(f"🛠️  Upserting Route53 A Alias: {name} -> {dns}")
    r53.change_resource_record_sets(HostedZoneId=hosted_zone_id, ChangeBatch=change_batch)
    _log("✅ Route53 record upsert submitted")


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-deploy domain configuration (CloudFront + API Gateway).")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--domain-name", default="repwarrior.net")
    parser.add_argument("--hosted-zone-id", default="Z0224155HV050F02RZE0")
    parser.add_argument("--storage-stack", default="ConsistencyTracker-Storage")
    parser.add_argument("--dns-stack", default="ConsistencyTracker-DNS")
    parser.add_argument("--api-stack", default="ConsistencyTracker-API")
    parser.add_argument("--stage-name", default="prod")
    parser.add_argument("--skip-cloudfront", action="store_true")
    parser.add_argument("--skip-api-domain", action="store_true")
    parser.add_argument("--wait", action="store_true", help="Wait for CloudFront deployments to finish.")
    args = parser.parse_args()

    cfg = Config(
        region=args.region,
        domain_name=args.domain_name,
        hosted_zone_id=args.hosted_zone_id,
        storage_stack=args.storage_stack,
        dns_stack=args.dns_stack,
        api_stack=args.api_stack,
        stage_name=args.stage_name,
        enable_cloudfront=not args.skip_cloudfront,
        enable_api_domain=not args.skip_api_domain,
        wait=args.wait,
    )

    session = boto3.Session(region_name=cfg.region)
    cf = session.client("cloudformation")
    cloudfront = session.client("cloudfront")  # global endpoint
    apigw = session.client("apigateway")
    r53 = session.client("route53")
    acm = session.client("acm")

    cert_arn = get_stack_output(cf, cfg.dns_stack, "CertificateArn")
    if not cert_arn:
        _die(f"Could not find CertificateArn output in stack '{cfg.dns_stack}'")

    cert = acm.describe_certificate(CertificateArn=cert_arn)["Certificate"]
    if cert.get("Status") != "ISSUED":
        _die(f"ACM certificate is not ISSUED yet (status={cert.get('Status')}). Try again in a minute.")

    _log(f"✅ Using ACM certificate: {cert_arn}")

    if cfg.enable_cloudfront:
        frontend_dist, content_dist = get_cloudfront_distribution_ids(cf, cfg.storage_stack)
        update_distribution_aliases_and_cert(
            cloudfront,
            frontend_dist,
            aliases=[cfg.domain_name, f"www.{cfg.domain_name}"],
            cert_arn=cert_arn,
        )
        update_distribution_aliases_and_cert(
            cloudfront,
            content_dist,
            aliases=[f"content.{cfg.domain_name}"],
            cert_arn=cert_arn,
        )
        if cfg.wait:
            wait_for_cloudfront_deployed(cloudfront, frontend_dist)
            wait_for_cloudfront_deployed(cloudfront, content_dist)

    if cfg.enable_api_domain:
        rest_api_id = get_rest_api_id(cf, cfg.api_stack)
        api_domain = f"api.{cfg.domain_name}"
        regional_domain, regional_zone = ensure_apigw_custom_domain_and_mapping(
            apigw,
            domain_name=api_domain,
            cert_arn=cert_arn,
            rest_api_id=rest_api_id,
            stage_name=cfg.stage_name,
        )
        upsert_route53_alias_a_record(
            r53,
            hosted_zone_id=cfg.hosted_zone_id,
            record_name=api_domain,
            target_dns_name=regional_domain,
            target_hosted_zone_id=regional_zone,
        )

    _log("\n🎉 Post-deploy configuration complete.")


if __name__ == "__main__":
    main()


