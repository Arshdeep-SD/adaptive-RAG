#!/usr/bin/env python3
"""
Seed the demo with 5 datasets, each targeting a distinct UI layout.
Run after the API is up: python scripts/seed_demo.py [--url http://localhost:8000]
"""
import argparse
import json
import time
import httpx

DEMO_DATASETS = [
    # 1. employees.csv → table + kpi
    {
        "name": "employees",
        "filename": "employees.csv",
        "content": b"""id,name,department,role,salary
1,Alice Johnson,Engineering,Senior Engineer,120000
2,Bob Smith,Engineering,Engineer,95000
3,Carol White,Product,Product Manager,115000
4,David Lee,Design,UI Designer,90000
5,Eva Martinez,Engineering,Tech Lead,140000
6,Frank Chen,Sales,Account Executive,85000
7,Grace Kim,HR,HR Manager,100000
8,Henry Brown,Engineering,Engineer,92000
9,Iris Davis,Product,Product Designer,105000
10,James Wilson,Marketing,Marketing Lead,98000
""",
        "content_type": "text/csv",
    },
    # 2. company_overview.txt → text + source_refs
    {
        "name": "company_overview",
        "filename": "company_overview.txt",
        "content": b"""Adaptive Data Systems -- Company Overview

Adaptive Data Systems (ADS) was founded in 2019 with the mission to democratize data intelligence for engineers and analysts. Our core platform combines retrieval-augmented generation with dynamic user interfaces, enabling teams to query complex datasets in natural language.

Our technology stack leverages state-of-the-art embedding models and large language models to provide grounded, citation-backed answers. We serve over 200 enterprise customers across financial services, healthcare, and technology sectors.

The company is headquartered in San Francisco with engineering offices in New York and Austin. We have raised $45M in Series B funding and are growing at 180% year-over-year.

Key product offerings:
- RAG Platform: enterprise knowledge retrieval
- Dynamic UI Engine: LLM-generated interfaces
- Data Connector Suite: 50+ pre-built integrations
- Analytics Dashboard: real-time usage metrics
""",
        "content_type": "text/plain",
    },
    # 3. sales_data.json → chart (line) + kpi
    {
        "name": "sales_data",
        "filename": "sales_data.json",
        "content": json.dumps([
            {"month": "Jan", "revenue": 120000, "units": 450, "region": "West"},
            {"month": "Feb", "revenue": 135000, "units": 510, "region": "West"},
            {"month": "Mar", "revenue": 148000, "units": 560, "region": "West"},
            {"month": "Apr", "revenue": 162000, "units": 612, "region": "West"},
            {"month": "May", "revenue": 178000, "units": 670, "region": "West"},
            {"month": "Jun", "revenue": 195000, "units": 735, "region": "West"},
            {"month": "Jul", "revenue": 189000, "units": 713, "region": "West"},
            {"month": "Aug", "revenue": 204000, "units": 768, "region": "West"},
            {"month": "Sep", "revenue": 221000, "units": 832, "region": "West"},
            {"month": "Oct", "revenue": 238000, "units": 895, "region": "West"},
            {"month": "Nov", "revenue": 255000, "units": 960, "region": "West"},
            {"month": "Dec", "revenue": 272000, "units": 1024, "region": "West"},
        ]).encode(),
        "content_type": "application/json",
    },
    # 4. incident_log.csv → timeline
    {
        "name": "incident_log",
        "filename": "incident_log.csv",
        "content": b"""id,time,severity,title,description,resolved
INC-001,2024-03-01 09:15,HIGH,Database connection timeout,Primary DB cluster experienced connection pool exhaustion during peak traffic,true
INC-002,2024-03-05 14:30,MEDIUM,API latency spike,P99 latency increased to 2800ms for 15 minutes,true
INC-003,2024-03-12 02:45,CRITICAL,Service outage,Complete service outage for 22 minutes due to failed deployment,true
INC-004,2024-03-15 11:00,LOW,Elevated error rate,Error rate increased from 0.1% to 1.2% for batch jobs,true
INC-005,2024-03-19 16:20,HIGH,Memory leak detected,Worker processes consuming 95% of available memory,true
INC-006,2024-03-22 08:50,MEDIUM,SSL certificate expiry warning,Certificate expiring in 7 days,false
""",
        "content_type": "text/csv",
    },
    # 5. product_catalog.json → card list
    {
        "name": "product_catalog",
        "filename": "product_catalog.json",
        "content": json.dumps([
            {"name": "RAG Platform", "category": "Core", "price": 2500, "description": "Enterprise knowledge retrieval with source citations", "status": "GA"},
            {"name": "Dynamic UI Engine", "category": "Core", "price": 1800, "description": "LLM-generated interfaces tailored to each query", "status": "GA"},
            {"name": "Data Connector Suite", "category": "Integration", "price": 950, "description": "50+ pre-built connectors for databases, APIs, and files", "status": "GA"},
            {"name": "Analytics Dashboard", "category": "Analytics", "price": 700, "description": "Real-time usage metrics and query analytics", "status": "Beta"},
            {"name": "Vector Store Pro", "category": "Infrastructure", "price": 1200, "description": "Managed vector database with automatic scaling", "status": "GA"},
        ]).encode(),
        "content_type": "application/json",
    },
]

DEMO_QUERIES = [
    "Show me the employee list and total headcount",
    "What is the company mission and background?",
    "Show me the sales trend over time",
    "What incidents occurred and when?",
    "List the available products",
]


def wait_for_job(client: httpx.Client, base_url: str, job_id: str, timeout: int = 60) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        resp = client.get(f"{base_url}/jobs/{job_id}")
        resp.raise_for_status()
        job = resp.json()
        if job["status"] in ("READY", "FAILED"):
            return job
        print(f"    [{job['status']}] waiting...")
        time.sleep(2)
    return {"status": "TIMEOUT"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print(f"Seeding demo data at {base}\n")

    job_ids = []
    with httpx.Client(timeout=30) as client:
        for ds in DEMO_DATASETS:
            print(f"Ingesting: {ds['filename']}")
            resp = client.post(
                f"{base}/ingest",
                files={"file": (ds["filename"], ds["content"], ds["content_type"])},
            )
            resp.raise_for_status()
            job = resp.json()
            job_ids.append((ds["name"], job["job_id"]))
            print(f"  Job ID: {job['job_id']}")

        print("\nWaiting for jobs to complete...")
        for name, job_id in job_ids:
            print(f"\n  {name} ({job_id}):")
            result = wait_for_job(client, base, job_id)
            status = result["status"]
            if status == "READY":
                print(f"    READY — {result.get('record_count', 0)} records")
            else:
                print(f"    {status}: {result.get('error', '')}")

        print("\n" + "=" * 50)
        print("Demo queries (run these to show distinct UI patterns):")
        for q in DEMO_QUERIES:
            print(f'  "{q}"')
        print("\nCache hit demo: run the same query twice — second response shows cache_hit: true")


if __name__ == "__main__":
    main()
